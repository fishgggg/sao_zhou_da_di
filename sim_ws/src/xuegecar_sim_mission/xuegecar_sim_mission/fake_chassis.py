#!/usr/bin/env python3
"""假底盘：在没有 Gazebo / 没有实车时，扮演「底盘驱动」的角色。

阶段 9.3 的验证工具，不是产品代码。
它存在的唯一理由：证明任务状态机**不关心**速度从哪来、里程计从哪来。

它做的事情正好等于一个真实底盘驱动：
  订阅 /cmd_vel_motor  → 积分出位姿 → 发布 /odom + TF(odom→base_footprint)
  同时按房间几何算一份 /scan

对比：
  Gazebo 场景：gazebo_ros_diff_drive 插件做同样的事（物理引擎算）
  实车场景   ：底盘 MCU 通过串口/CAN 收速度，回传编码器/IMU，驱动节点算出 odom
  本节点     ：纯数学积分，无物理、无碰撞

⚠️ 只能用于验证链路与状态机，**不可用于导航**（没有真实碰撞，车能穿墙）。
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformBroadcaster


class FakeChassis(Node):
    def __init__(self):
        super().__init__('fake_chassis')

        self.declare_parameter('room_half_size', 2.0)   # 4x4 房间，墙在 ±2.0
        self.declare_parameter('odom_rate', 50.0)
        self.declare_parameter('scan_rate', 10.0)
        self.declare_parameter('scan_samples', 360)

        self.half = float(self.get_parameter('room_half_size').value)
        self.n_samples = int(self.get_parameter('scan_samples').value)
        odom_rate = float(self.get_parameter('odom_rate').value)
        scan_rate = float(self.get_parameter('scan_rate').value)

        # 位姿与速度（差速运动学状态）
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.v = 0.0
        self.w = 0.0

        # 与真实底盘驱动完全相同的接口
        self.create_subscription(Twist, 'cmd_vel_motor', self.on_cmd, 10)
        self.odom_pub = self.create_publisher(Odometry, 'odom', 20)
        self.scan_pub = self.create_publisher(LaserScan, 'scan', 10)
        self.tf_pub = TransformBroadcaster(self)

        self.dt = 1.0 / odom_rate
        self.create_timer(self.dt, self.step_odom)
        self.create_timer(1.0 / scan_rate, self.publish_scan)

        self.get_logger().info(
            f'假底盘启动：房间 ±{self.half} m，odom {odom_rate:.0f} Hz，'
            f'scan {scan_rate:.0f} Hz。只用于验证抽象层，不可用于导航。')

    # ---------- 收速度 ----------
    def on_cmd(self, msg: Twist):
        self.v = msg.linear.x
        self.w = msg.angular.z

    # ---------- 积分出 odom ----------
    def step_odom(self):
        # 差速运动学（与真实底盘一致的最简模型）
        self.x += self.v * math.cos(self.theta) * self.dt
        self.y += self.v * math.sin(self.theta) * self.dt
        self.theta += self.w * self.dt

        # 撞墙就把车按在墙上（不穿墙），速度清零
        if abs(self.x) > self.half - 0.05:
            self.x = math.copysign(self.half - 0.05, self.x)
            self.v = 0.0
        if abs(self.y) > self.half - 0.05:
            self.y = math.copysign(self.half - 0.05, self.y)
            self.v = 0.0

        now = self.get_clock().now().to_msg()

        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.theta / 2.0)
        odom.twist.twist.linear.x = self.v
        odom.twist.twist.angular.z = self.w
        self.odom_pub.publish(odom)

        tf = TransformStamped()
        tf.header.stamp = now
        tf.header.frame_id = 'odom'
        tf.child_frame_id = 'base_footprint'
        tf.transform.translation.x = self.x
        tf.transform.translation.y = self.y
        tf.transform.rotation.z = math.sin(self.theta / 2.0)
        tf.transform.rotation.w = math.cos(self.theta / 2.0)
        self.tf_pub.sendTransform(tf)

    # ---------- 按房间几何算 scan ----------
    def _ray(self, angle):
        """从 (x,y) 沿 angle 打一条射线，返回撞到四面墙的距离。"""
        dx, dy = math.cos(angle), math.sin(angle)
        best = float('inf')
        for wall in (self.half, -self.half):
            if abs(dx) > 1e-9:
                t = (wall - self.x) / dx
                if t > 0 and abs(self.y + t * dy) <= self.half:
                    best = min(best, t)
            if abs(dy) > 1e-9:
                t = (wall - self.y) / dy
                if t > 0 and abs(self.x + t * dx) <= self.half:
                    best = min(best, t)
        return best

    def publish_scan(self):
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = 'laser_frame'
        scan.angle_min = -math.pi
        scan.angle_max = math.pi
        scan.angle_increment = 2.0 * math.pi / self.n_samples
        scan.range_min = 0.05
        scan.range_max = 12.0
        scan.ranges = [
            min(self._ray(-math.pi + i * scan.angle_increment), 12.0)
            for i in range(self.n_samples)
        ]
        self.scan_pub.publish(scan)


def main(args=None):
    rclpy.init(args=args)
    node = FakeChassis()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
