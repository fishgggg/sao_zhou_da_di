#!/usr/bin/env python3
"""任务状态机 · 阶段 8.6（接 Nav2 Action）

8.1 闸门 → 8.2 骨架 → 8.3 急停 → 8.4 看门狗 → 8.5 迁移表/分权 → **8.6 接 Nav2**

这一步让状态机从「被动听速度」变成「主动发任务」：
  收到目标点 → 校验准入 → 调 NavigateToPose → 跟踪结果
  成功 → IDLE ；失败 → ERROR ；中途切走 → 取消目标

三个新概念：
  1. Action ≠ Topic：有 goal / feedback / result 三段，走 goal_handle 生命周期
  2. 异步：send_goal_async 返回 future，不能阻塞 spin（否则整个节点卡死）
  3. 取消是义务：状态离开 NAVIGATING 必须 cancel，否则车会一直跑到终点

七个状态与分权表（8.5）保持不变。
"""

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Twist, PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus


class MissionControl(Node):
    STATES = ('IDLE', 'TELEOP', 'MAPPING', 'LOCALIZING', 'NAVIGATING', 'ESTOP', 'ERROR')

    # ---------- 分权：每个状态只听一个源 ----------
    SOURCE_BY_STATE = {
        'TELEOP': 'teleop',        # /cmd_vel_teleop
        'MAPPING': 'teleop',
        'NAVIGATING': 'nav',       # /cmd_vel（Nav2 的输出）
    }
    VELOCITY_ALLOWED = set(SOURCE_BY_STATE)

    # ---------- 迁移表 ----------
    ALLOWED = {
        'IDLE':       {'TELEOP', 'MAPPING', 'LOCALIZING', 'NAVIGATING'},
        'TELEOP':     {'IDLE'},
        'MAPPING':    {'IDLE'},
        'LOCALIZING': {'IDLE'},
        'NAVIGATING': {'IDLE'},   # 只能回 IDLE（取消导航）
        'ESTOP':      set(),
        'ERROR':      set(),
    }
    ALWAYS_ENTERABLE = {'ESTOP'}
    REQUIRE_DATA = {'TELEOP', 'MAPPING', 'NAVIGATING'}
    SAFETY_HOLD = {'ESTOP', 'ERROR'}
    STICKY = {'ESTOP', 'ERROR'}
    WATCHDOG_ACTIVE_IN = {'TELEOP', 'MAPPING', 'NAVIGATING'}
    MONITORED = ('odom', 'scan')

    SAFETY_HZ = 20.0
    WATCHDOG_HZ = 10.0

    # 目标被 Nav2 接受的最长等待。超时说明 bt_navigator 卡了。
    GOAL_ACCEPT_TIMEOUT = 10.0

    def __init__(self):
        super().__init__('mission_control')

        self.state = 'IDLE'
        self.forwarded = 0
        self.blocked = {'teleop': 0, 'nav': 0}
        self.zero_sent = 0
        self.estop_entered = 0
        self.error_entered = 0

        # ---- 看门狗参数 ----
        self.declare_parameter('odom_timeout', 0.5)
        self.declare_parameter('scan_timeout', 1.0)
        self.declare_parameter('grace_period', 5.0)
        # 启动时进入哪个状态（阶段 9：省掉每次手切 TELEOP）。
        # 只允许非粘性状态，ESTOP/ERROR 必须由事件触发。
        self.declare_parameter('initial_state', 'IDLE')
        self.timeouts = {
            'odom': float(self.get_parameter('odom_timeout').value),
            'scan': float(self.get_parameter('scan_timeout').value),
        }
        self.grace = float(self.get_parameter('grace_period').value)
        self.start_time = time.monotonic()
        self.last_rx = {}

        # ---- 速度入口（8.5 分权）----
        self.create_subscription(Twist, 'cmd_vel_teleop', self.on_teleop_cmd, 10)
        self.create_subscription(Twist, 'cmd_vel', self.on_nav_cmd, 10)

        # ---- 唯一速度出口 ----
        self.motor_pub = self.create_publisher(Twist, 'cmd_vel_motor', 10)

        # ---- 状态 ----
        self.state_pub = self.create_publisher(String, 'mission_state', 10)
        self.create_subscription(String, 'mission_command', self.on_command, 10)

        # ---- 目标点：一条 PoseStamped 消息（RViz 的 2D Goal Pose 也发这个）----
        self.create_subscription(PoseStamped, 'mission_goal', self.on_mission_goal, 10)

        # ---- 被监控的数据源 ----
        self.create_subscription(Odometry, 'odom', self.on_odom, 20)
        self.create_subscription(LaserScan, 'scan', self.on_scan, 20)

        # ---- Nav2 客户端 ----
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._nav_goal_handle = None
        self._nav_goal_future = None
        self._nav_sent_at = None
        self._nav_feedback_count = 0
        self._nav_goal_xy = None          # 目标在 map 系下的坐标
        self.amcl_xy = None               # AMCL 认为车在 map 系的位置

        # AMCL 位姿：用来识别「Nav2 报成功但车其实没到」的假成功
        self.create_subscription(
            PoseWithCovarianceStamped, 'amcl_pose', self.on_amcl, 10)

        # ---- 定时器 ----
        self.create_timer(1.0 / self.SAFETY_HZ, self.enforce_safe)
        self.create_timer(1.0 / self.WATCHDOG_HZ, self.check_links)
        self.create_timer(1.0, self.tick)

        # ---- 启动自检：防止同一节点多实例 ----
        self._unique_checked = False
        self.create_timer(1.0, self.check_unique)

        # ---- 初始状态（可被 launch 参数覆盖）----
        init = str(self.get_parameter('initial_state').value).strip().upper()
        if init in self.STATES and init not in self.STICKY:
            self.state = init
        else:
            self.get_logger().warn(
                f'initial_state={init!r} 不合法（只允许 '
                f'{[s for s in self.STATES if s not in self.STICKY]}），回退 IDLE')
            self.state = 'IDLE'

        self.publish_state()
        self.get_logger().info(
            f'mission_control 启动：state={self.state}，放行={sorted(self.VELOCITY_ALLOWED)}')
        self.get_logger().info(
            '分权表：' + '、'.join(f'{s}→{src}' for s, src in self.SOURCE_BY_STATE.items()))
        self.get_logger().info(
            f'看门狗：仅在 {sorted(self.WATCHDOG_ACTIVE_IN)} 监控；'
            f'odom>{self.timeouts["odom"]}s、scan>{self.timeouts["scan"]}s → ERROR')
        self.get_logger().info(
            '发导航目标（PoseStamped → /mission_goal）：\n'
            '  ros2 topic pub --once /mission_goal geometry_msgs/msg/PoseStamped '
            '"{header: {frame_id: map}, pose: {position: {x: 1.5, y: 1.0}, '
            'orientation: {w: 1.0}}}"')
        self.get_logger().info(
            '⚠️ teleop 必须改话题：--ros-args -r cmd_vel:=cmd_vel_teleop')

    # ================= 速度闸门（8.5）=================
    def on_teleop_cmd(self, msg: Twist):
        self._gate(msg, 'teleop')

    def on_nav_cmd(self, msg: Twist):
        self._gate(msg, 'nav')

    def _gate(self, msg: Twist, source: str):
        if self.SOURCE_BY_STATE.get(self.state) != source:
            self.blocked[source] += 1
            return
        self.motor_pub.publish(msg)
        self.forwarded += 1

    # ================= 数据心跳 =================
    def on_odom(self, msg: Odometry):
        self.last_rx['odom'] = time.monotonic()

    def on_scan(self, msg: LaserScan):
        self.last_rx['scan'] = time.monotonic()

    def on_amcl(self, msg: PoseWithCovarianceStamped):
        p = msg.pose.pose.position
        self.amcl_xy = (p.x, p.y)

    # ================= Nav2 目标 =================
    def on_mission_goal(self, msg: PoseStamped):
        """收到目标点：这是进入 NAVIGATING 的**唯一**正式入口。"""
        if self.state != 'IDLE':
            self.get_logger().warn(
                f'拒绝新目标：当前 {self.state}，只有 IDLE 能接任务（先回 IDLE）')
            return

        bad = self.faults_cleared()
        if bad:
            detail = '、'.join(f'/{n}（{self.timeouts[n]:.1f}s 内无数据）' for n in bad)
            self.get_logger().error(f'拒绝目标：数据不健康 —— {detail}')
            return

        if not self.nav_client.server_is_ready():
            self.get_logger().error(
                '拒绝目标：Nav2 的 /navigate_to_pose 不在线。'
                '先启动 nav2_bringup（见了 map_server / bt_navigator 才有服务）')
            return

        p = msg.pose.position
        self._nav_goal_xy = (p.x, p.y)
        self.get_logger().info(f'收到目标 ({p.x:.2f}, {p.y:.2f})，开始导航')

        self._set_state('NAVIGATING')

        goal = NavigateToPose.Goal()
        goal.pose = msg
        self._nav_sent_at = time.monotonic()
        self._nav_feedback_count = 0
        self._nav_goal_future = self.nav_client.send_goal_async(
            goal, feedback_callback=self._on_nav_feedback)
        self._nav_goal_future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        """Nav2 决定接不接受这个目标。"""
        try:
            goal_handle = future.result()
        except Exception as exc:                      # noqa: BLE001
            self.get_logger().error(f'发送目标失败：{exc} → ERROR')
            self._set_state('ERROR')
            return

        if not goal_handle.accepted:
            self.get_logger().error('目标被 Nav2 拒绝 → ERROR')
            self._set_state('ERROR')
            return

        self._nav_goal_handle = goal_handle
        self.get_logger().info('目标已被接受，开始执行')
        goal_handle.get_result_async().add_done_callback(self._on_nav_result)

    def _on_nav_feedback(self, feedback_msg):
        self._nav_feedback_count += 1
        # 行为树反馈里带剩余距离等信息；每 20 帧打一次，避免刷屏
        if self._nav_feedback_count % 20 == 1:
            fb = feedback_msg.feedback
            dist = getattr(fb, 'distance_remaining', None)
            if dist is not None:
                self.get_logger().info(f'导航中：剩余 {dist:.2f} m')

    def _on_nav_result(self, future):
        """目标结束（成功 / 失败 / 被取消）。"""
        status = future.result().status
        self._nav_goal_handle = None
        self._nav_goal_future = None
        self._nav_sent_at = None

        if status == GoalStatus.STATUS_SUCCEEDED:
            self._warn_if_fake_success()
            self.get_logger().info('导航成功 → IDLE')
            if self.state == 'NAVIGATING':
                self._set_state('IDLE')
        elif status == GoalStatus.STATUS_CANCELED:
            # 状态已被触发取消的那条路径改掉，这里只记录
            self.get_logger().warn('导航已取消')
        else:
            names = {
                GoalStatus.STATUS_ABORTED: 'ABORTED',
                GoalStatus.STATUS_UNKNOWN: 'UNKNOWN',
            }
            self.get_logger().error(
                f'导航失败 status={status}（{names.get(status, "?")}） → ERROR')
            if self.state == 'NAVIGATING':
                self._set_state('ERROR')

    def _warn_if_fake_success(self):
        """Nav2 报成功时核对一下：车真的到目标附近了吗？

        实测踩过：Nav2 在 abort 之后可能残留异常状态，收到目标立刻回 SUCCEEDED，
        日志表现为「导航中：剩余 0.00 m」后 60 ms 就成功，而车一步没动。
        用 AMCL 位姿与目标比一下，把这种「假成功」变成可见的警告。
        """
        if self.amcl_xy is None or self._nav_goal_xy is None:
            return
        d = math.hypot(self.amcl_xy[0] - self._nav_goal_xy[0],
                       self.amcl_xy[1] - self._nav_goal_xy[1])
        if d > 0.8:
            self.get_logger().warn(
                f'⚠️ 疑似假成功：Nav2 报 SUCCEEDED，但 AMCL 显示车在 '
                f'({self.amcl_xy[0]:.2f}, {self.amcl_xy[1]:.2f})，'
                f'距目标 ({self._nav_goal_xy[0]:.2f}, {self._nav_goal_xy[1]:.2f}) '
                f'还有 {d:.2f} m。通常是 Nav2 实例状态异常（abort 残留），重启 Nav2 再试。')

    def _cancel_navigation(self):
        """离开 NAVIGATING 时必须取消目标，否则车会继续跑到终点。"""
        if self._nav_goal_handle is not None:
            self.get_logger().warn('取消进行中的导航目标')
            self._nav_goal_handle.cancel_goal_async()
            self._nav_goal_handle = None
        self._nav_goal_future = None
        self._nav_sent_at = None

    # ================= 启动自检 =================
    def check_unique(self):
        if self._unique_checked:
            return
        self._unique_checked = True
        others = self.count_publishers('cmd_vel_motor')   # 把自己也算进去
        if others > 1:
            self.get_logger().fatal(
                f'启动中止：/cmd_vel_motor 上已有 {others} 个发布者。'
                f'说明有旧的 mission_control 没退出——两个控制器同时发速度会让车抖动。')
            raise RuntimeError('duplicate mission_control')

    # ================= 看门狗 =================
    def check_links(self):
        if self.state not in self.WATCHDOG_ACTIVE_IN:
            return
        now = time.monotonic()
        if now - self.start_time < self.grace:
            return
        for name in self.MONITORED:
            last = self.last_rx.get(name)
            age = (now - last) if last is not None else (now - self.start_time)
            if age > self.timeouts[name]:
                self._set_state('ERROR')
                self.get_logger().error(
                    f'!!! 看门狗：/{name} 已 {age:.2f}s 无数据'
                    f'（阈值 {self.timeouts[name]:.2f}s）→ ERROR，已强制零速')
                return

    def _link_ok(self, name, now):
        last = self.last_rx.get(name)
        return last is not None and (now - last) <= self.timeouts[name]

    def faults_cleared(self):
        now = time.monotonic()
        return [n for n in self.MONITORED if not self._link_ok(n, now)]

    # ================= 安全回路 =================
    def enforce_safe(self):
        if self.state in self.SAFETY_HOLD:
            self._publish_zero()

    def _publish_zero(self):
        self.motor_pub.publish(Twist())
        self.zero_sent += 1

    # ================= 状态迁移 =================
    def on_command(self, msg: String):
        target = msg.data.strip().upper()

        if target == 'RESET':
            if self.state not in self.STICKY:
                self.get_logger().warn(
                    f'RESET 只在 {" / ".join(sorted(self.STICKY))} 下有效，当前 {self.state}')
                return
            if self.state == 'ERROR':
                bad = self.faults_cleared()
                if bad:
                    detail = '、'.join(
                        f'/{n}（{self.timeouts[n]:.1f}s 内无数据）' for n in bad)
                    self.get_logger().error(f'拒绝复位：故障未消除 —— {detail}')
                    return
            self._set_state('IDLE')
            return

        if target not in self.STATES:
            self.get_logger().warn(
                f'拒绝迁移：未知状态 {target!r}（支持 {self.STATES} + RESET）')
            return

        if self.state in self.STICKY and target not in self.STICKY:
            self.get_logger().error(
                f'拒绝迁移：{self.state} 是粘性状态，必须先发 RESET')
            return

        if target == self.state:
            self.get_logger().info(f'已经在 {target}，忽略')
            return

        if target not in self.ALWAYS_ENTERABLE:
            allowed = self.ALLOWED.get(self.state, set())
            if target not in allowed:
                self.get_logger().error(
                    f'拒绝迁移：{self.state} → {target} 不在迁移表里；'
                    f'当前允许 {sorted(allowed) or "无（先 RESET）"}')
                return

        if target in self.REQUIRE_DATA:
            bad = self.faults_cleared()
            if bad:
                detail = '、'.join(
                    f'/{n}（{self.timeouts[n]:.1f}s 内无数据）' for n in bad)
                self.get_logger().error(
                    f'拒绝迁移：进入 {target} 需要数据健康，但 {detail}。'
                    f'先确认仿真/底盘已启动')
                return

        # 手动进 NAVIGATING：允许，但没有目标车不会动
        if target == 'NAVIGATING':
            self.get_logger().warn(
                '手动进入 NAVIGATING：没有目标点，车不会动。'
                '正常做法是往 /mission_goal 发 PoseStamped')

        self._set_state(target)

    def _set_state(self, target):
        previous = self.state

        # 离开 NAVIGATING 必须取消目标
        if previous == 'NAVIGATING' and target != 'NAVIGATING':
            self._cancel_navigation()

        self.state = target

        if target not in self.VELOCITY_ALLOWED:
            self._publish_zero()

        if target == 'ESTOP':
            self.estop_entered += 1
            self.get_logger().error(
                f'!!! 急停：{previous} → ESTOP，已强制零速；必须 RESET 才能恢复')

        if target == 'ERROR':
            self.error_entered += 1

        self.publish_state()
        src = self.SOURCE_BY_STATE.get(target)
        self.get_logger().info(f'{previous} → {target}（听={src or "无"}）')

    # ================= 周期性 =================
    def tick(self):
        self.publish_state()

        # 目标发出后迟迟没被接受 → Nav2 可能卡住
        if (self.state == 'NAVIGATING' and self._nav_goal_handle is None
                and self._nav_sent_at is not None
                and time.monotonic() - self._nav_sent_at > self.GOAL_ACCEPT_TIMEOUT):
            self.get_logger().error(
                f'目标 {self.GOAL_ACCEPT_TIMEOUT:.0f}s 未被接受 → ERROR')
            self._set_state('ERROR')
            return

        if self.state == 'ERROR':
            bad = self.faults_cleared()
            msg = ('数据已恢复，可以 RESET' if not bad
                   else f'故障源={"、".join(bad)}（等数据恢复 + RESET）')
            self.get_logger().warn(
                f'state=ERROR {msg} 零速已发={self.zero_sent} 帧',
                throttle_duration_sec=2.0)
        elif self.state in self.SAFETY_HOLD:
            self.get_logger().warn(
                f'state={self.state} 零速已发={self.zero_sent} 帧，'
                f'拦截(teleop={self.blocked["teleop"]} nav={self.blocked["nav"]})（持续压零速）',
                throttle_duration_sec=2.0)
        else:
            now = time.monotonic()
            ages = ' '.join(
                f'{n}={now - self.last_rx[n]:.2f}s' if n in self.last_rx else f'{n}=未见'
                for n in self.MONITORED)
            src = self.SOURCE_BY_STATE.get(self.state) or '无'
            self.get_logger().info(
                f'state={self.state} 听={src} 转发={self.forwarded} '
                f'拦截(teleop={self.blocked["teleop"]} nav={self.blocked["nav"]}) [{ages}]',
                throttle_duration_sec=5.0)

            if self.state == 'TELEOP' and self.blocked['nav'] > 0:
                self.get_logger().warn(
                    f'TELEOP 状态下拦下了 {self.blocked["nav"]} 条 nav 源速度。'
                    f'如果你用的是 teleop，请确认启动时加了 -r cmd_vel:=cmd_vel_teleop',
                    throttle_duration_sec=10.0)

    def publish_state(self):
        self.state_pub.publish(String(data=self.state))


def main(args=None):
    rclpy.init(args=args)
    node = MissionControl()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except RuntimeError as exc:
        node.get_logger().fatal(f'退出：{exc}')
        node.destroy_node()
        rclpy.shutdown()
        raise SystemExit(1) from None
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
