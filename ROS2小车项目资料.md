# ROS2 小车项目资料

> 记录时间：2026-09-08
> 说明：本文档基于源码静态阅读整理，未连接真实硬件联调。

## 1. 项目定位

这是一个完整的 ROS 2 差速小车系统，不只是单一控制程序，而是由“ROS 2 上位机 + ESP32 底盘 MCU + 独立 ESP32 摄像头”组成的移动机器人平台。

项目分成两大部分：

- `xuegeros_ws`：ROS 2 上位机工作区
- `leap_demo`：底盘和摄像头的 ESP32 固件工程

## 2. 总体架构

```text
Qt GUI / Nav2 / SLAM / 键盘控制
                |
                v
           ROS 2 话题与服务
                |
      /cmd_vel /odom /scan /imu
                |
   micro-ROS 或 MAVLink 通信层
                |
                v
        ESP32-S3 底盘主控固件
                |
       速度控制 + 差速运动学
                |
     电机 / 编码器 / IMU / 雷达
```

摄像头链路：

```text
ESP32 摄像头 -> HTTP MJPEG -> ROS 图像话题 -> Qt 界面显示
```

## 3. 实现了什么功能

### 3.1 底盘运动控制

支持：

- 前进、后退、转向
- 左右轮独立控制
- 速度模式
- 绝对位置模式
- 相对距离与角度运动
- 急停与刹车
- 最大加速度限制
- 速度滤波
- 电机死区补偿
- 里程计复位

### 3.2 传感器采集

底盘支持：

- 左右轮编码器
- LSM6DS3 IMU
- Camsense 激光雷达
- HC-SR04 超声波
- 电池电压检测
- 舵机控制

### 3.3 ROS 侧功能

ROS 工程提供：

- Qt 图形界面
- 手动遥控
- 发送导航目标
- 初始位姿设置
- 地图显示
- 轨迹显示
- 雷达显示
- 摄像头显示
- SLAM 建图
- Nav2 自动导航
- MAVLink 桥接
- 摄像头图像转发

### 3.4 摄像头功能

`leap_cam` 是独立的 ESP32 摄像头工程，具备：

- OV3660 摄像头采集
- JPEG 输出
- HTTP MJPEG 视频流
- Wi-Fi 配网页面
- 与底盘通过 I2C 通信

## 4. 工程框架

### 4.1 ROS 2 工作区 `xuegeros_ws`

主要包包括：

- `xuegecar_bringup`
- `xuegecar_description`
- `xuegecar_mavlink_bridge`
- `xuegecar_camera`
- `xuegecar_cartographer`
- `xuegecar_navigation2`
- `slam_gmapping`
- `camsense_lidar`
- `xuegecar_qt_gui`
- `xuegecar_servo_qt_gui`
- `leap_interfaces`
- `xuegeros_demo`

### 4.2 底盘固件 `leap_ros_mcu_driver`

核心启动流程：

1. 初始化 NVS
2. 读取设备名、Wi-Fi 和通信模式
3. 读取速度 PID
4. 初始化硬件与 I2C 资源
5. 创建队列
6. 启动传感器与控制任务
7. 启动 micro-ROS 或 MAVLink 通信任务

主要任务：

- `imu_task`
- `motion_task`
- `ultrasonic_task`
- `battery_task`
- `peripheral_task`
- `lidar_task`
- `camera_task`
- `wifi_start_task`

### 4.3 摄像头固件 `leap_cam`

启动内容包括：

- 板级控制
- Wi-Fi 管理
- I2C 从机通信
- 摄像头初始化
- 配网页面服务
- MJPEG 视频服务
- UDP 发现服务

## 5. 通信方式

底盘支持三种互斥通信模式：

1. micro-ROS
2. MAVLink UDP
3. MAVLink UART

### 5.1 micro-ROS

订阅：

- `/cmd_vel`

发布：

- `/odom`
- `/imu`
- `/scan`
- `/battery_state`
- `/ultrasonic`

服务：

- `/set_speed_pid`
- `/get_speed_pid`

### 5.2 MAVLink

支持的控制与配置包括：

- 速度控制
- 舵机控制
- 急停/解锁
- 里程计复位
- PID 参数设置
- 自定义相对运动

## 6. 开源者留下的改动接口

### 6.1 硬件接线修改

最重要文件：

- `leap_ros_mcu_driver/main/platform/board.cpp`
- `leap_cam/main/camera_init.c`
- `leap_cam/main/i2c_slave_comm.h`
- `leap_cam/main/board_control.c`

可改内容：

- 电机 GPIO
- 编码器 GPIO
- 雷达串口引脚
- 超声波引脚
- 舵机引脚
- 状态灯引脚
- BOOT 按键
- 电池 ADC 通道
- IMU I2C 引脚
- 摄像头引脚与工作模式

### 6.2 车体尺寸与运动学

文件：

- `leap_ros_mcu_driver/main/control/motion_controller.cpp`

可改内容：

- 轮径
- 轮距
- 编码器每圈脉冲数
- 左右轮方向
- 最大速度
- 最大加速度
- 电机死区
- 位置误差阈值

### 6.3 PID 调参

文件：

- `leap_ros_mcu_driver/main/config/pid_config.cpp`
- `leap_ros_mcu_driver/main/control/motion_controller.cpp`
- `leap_ros_mcu_driver/main/tasks/network/microros_task.cpp`
- `leap_ros_mcu_driver/main/tasks/network/mavlink_common.cpp`

可通过 ROS 服务或 MAVLink 动态修改。

### 6.4 话题和消息接口

文件：

- `leap_ros_mcu_driver/main/tasks/network/microros_task.cpp`
- `xuegecar_mavlink_bridge/config/mavlink_bridge.yaml`
- `leap_interfaces/srv/*.srv`

### 6.5 传感器处理

文件：

- `leap_ros_mcu_driver/main/tasks/sensors/imu_task.cpp`
- `leap_ros_mcu_driver/main/tasks/sensors/lidar_task.cpp`
- `leap_ros_mcu_driver/main/tasks/sensors/ultrasonic_task.cpp`
- `leap_ros_mcu_driver/main/tasks/sensors/battery_task.cpp`

可改采样频率、发布频率、滤波、坐标方向、单位换算。

### 6.6 摄像头与视频

文件：

- `leap_cam/main/camera_init.c`
- `leap_cam/main/web_mjpeg.c`
- `leap_cam/main/web_config.c`
- `leap_cam/main/i2c_slave_comm.c`
- `xuegecar_camera/http_video_publisher.py`

### 6.7 Wi-Fi 与通信模式

文件：

- `leap_ros_mcu_driver/main/network/wifi_app.cpp`
- `leap_ros_mcu_driver/main/core/system_globals.cpp`
- `leap_cam/main/wifi_manager.c`

## 7. 主要接口清单

### ROS 侧常见话题

- `/cmd_vel`
- `/odom`
- `/imu`
- `/scan`
- `/battery_state`
- `/ultrasonic`
- `/camera/image_raw/compressed`
- `/goal_pose`
- `/initialpose`

### 常见服务

- `/set_speed_pid`
- `/get_speed_pid`

### 常见 frame

- `odom`
- `base_link`
- `imu_link`
- `laser_frame`
- `ultrasonic_link`

## 8. 使用时要注意的风险

- MAVLink UART 波特率配置存在不一致，必须统一。
- UART0 同时用于日志和 MAVLink，可能互相干扰。
- micro-ROS 默认 Agent 地址需要和实际电脑 IP 一致。
- `/odom` 和 TF 可能存在重复发布风险。
- 雷达方向经过多处转换，需用 RViz 现场确认。
- IMU 没有磁力计，yaw 会随时间漂移。
- 电池百分比只是线性估算，不是精确电量模型。
- `leap_cam` 是独立固件，不是 ROS 节点。

## 9. 一句话总结

这是一个可用于遥控、建图、导航、传感器采集和视频监控的 ROS 2 差速小车平台；`leap_demo` 提供底层固件，`xuegeros_ws` 提供上位机能力，二者通过 micro-ROS / MAVLink / HTTP 视频流组合成完整系统。
