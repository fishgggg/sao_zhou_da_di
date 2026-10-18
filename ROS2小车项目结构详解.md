# ROS2 小车项目结构详解

> 整理日期：2026-09-18  
> 本文依据当前本地源码目录整理，用于阅读代码、定位功能和后续二次开发。项目由 ROS 2 上位机、ESP32-S3 底盘固件和 ESP32 摄像头固件三部分组成。

## 1. 源码所在位置

### 1.1 ROS 2 上位机工作区

```text
C:\Users\Y\Desktop\ros_car\xuegeros_ws\xuegeros_ws
```

真正需要阅读和修改的 ROS 2 源码位于：

```text
C:\Users\Y\Desktop\ros_car\xuegeros_ws\xuegeros_ws\src
```

工作区中的目录含义：

```text
xuegeros_ws/
├── src/       # 所有 ROS 2 功能包的源代码，重点阅读
├── build/     # colcon 编译产生的中间文件，一般不修改
├── install/   # 编译安装结果，一般不修改
└── log/       # 编译和运行日志，一般不修改
```

不要在 `build` 或 `install` 中修改代码，因为重新编译后更改可能被覆盖。

### 1.2 ESP32 底盘和摄像头工程

```text
C:\Users\Y\Desktop\ros_car\leap_demo
```

其中：

```text
leap_demo/
├── leap_ros_mcu_driver/  # ESP32-S3 底盘固件
└── leap_cam/             # 独立 ESP32 摄像头固件
```

## 2. 一个 ROS 2 功能包通常如何组织

```text
功能包名称/
├── package.xml       # 包信息以及构建、运行依赖声明
├── CMakeLists.txt    # C/C++ 功能包的编译和安装规则
├── setup.py          # Python 功能包的安装及节点入口
├── setup.cfg         # Python 节点的安装路径配置
├── include/          # C/C++ 头文件：类、函数和公共接口声明
├── src/              # C/C++ 实现代码、节点主程序
├── launch/           # 组织并启动节点、参数及其他 launch
├── config/ 或 param/ # YAML 参数配置
├── urdf/             # 机器人连杆、关节及坐标系模型
├── meshes/           # URDF 使用的三维模型
├── rviz/             # RViz 显示配置
├── msg/              # 自定义消息定义
├── srv/              # 自定义服务定义
├── action/           # 自定义动作定义
└── README.md         # 使用说明
```

需要注意：

- `include` 不是第三方依赖安装目录，而是本功能包的 C/C++ 头文件目录。
- `src` 不是“静态代码”目录，而是功能和节点的实际实现代码目录。
- `launch` 不实现核心算法；它负责决定启动哪些节点、加载哪些参数，以及是否包含其他 launch 文件。
- 功能包不必包含以上全部目录，只保留它需要的部分。
- Python 包通常没有 `include`，Python 模块目录本身就是源代码目录。

## 3. ROS 2 工作区总体结构

```text
src/
├── xuegeros_demo/             # 整机示例与总启动入口
├── xuegecar_description/      # URDF 机器人模型和 TF 骨架
├── xuegecar_bringup/          # 机器人状态和 odom TF 启动
├── leap_interfaces/           # PID 相关自定义 ROS 服务
├── xuegecar_mavlink_bridge/   # MAVLink 与 ROS 2 的双向桥
├── camsense_lidar/            # Camsense 串口雷达 ROS 2 驱动
├── xuegecar_camera/           # HTTP/MJPEG 视频转 ROS 图像
├── slam_gmapping/             # GMapping 的 ROS 2 封装
├── openslam_gmapping/         # GMapping 底层算法库
├── xuegecar_cartographer/     # Cartographer 建图配置与启动
├── xuegecar_navigation2/      # Nav2 定位、规划和导航配置
├── xuegecar_qt_gui/           # 小车主控制与监视界面
└── xuegecar_servo_qt_gui/     # 舵机单独调试界面
```

可以按照职责将这些包分成五层：

| 层级    | 功能包                                                                                | 作用              |
| ----- | ---------------------------------------------------------------------------------- | --------------- |
| 启动与模型 | `xuegeros_demo`、`xuegecar_bringup`、`xuegecar_description`                          | 组织启动、模型和 TF     |
| 硬件接入  | `xuegecar_mavlink_bridge`、`camsense_lidar`、`xuegecar_camera`                       | 将底盘和传感器接入 ROS 2 |
| 接口定义  | `leap_interfaces`                                                                  | 定义 PID 服务的数据格式  |
| 算法    | `slam_gmapping`、`openslam_gmapping`、`xuegecar_cartographer`、`xuegecar_navigation2` | 建图、定位和导航        |
| 人机界面  | `xuegecar_qt_gui`、`xuegecar_servo_qt_gui`                                          | 显示状态并发送操作命令     |

## 4. 各 ROS 2 功能包详解

### 4.1 `xuegeros_demo`：整机总启动

```text
xuegeros_demo/
├── launch/
│   └── bringup_all.launch.py
├── CMakeLists.txt
└── package.xml
```

`bringup_all.launch.py` 是当前最接近“整车一键启动”的入口，依次处理：

1. 使用 `socat` 将 UDP 雷达数据映射成 `/dev/lidar`。
2. 启动 micro-ROS Agent，接收 ESP32 底盘数据。
3. 延迟启动 YDLIDAR 驱动。
4. 延迟启动 `xuegecar_bringup`。

它针对真实硬件编写，含设备路径和 sudo 密码等硬编码，不是仿真启动文件。

### 4.2 `xuegecar_description`：机器人模型

```text
xuegecar_description/
├── urdf/
│   └── xuegecar.urdf
├── CMakeLists.txt
└── package.xml
```

URDF 描述以下连杆与关节：

- `base_footprint`：机器人落地投影坐标系。
- `base_link`：底盘主体坐标系。
- `laser_frame`：雷达坐标系。
- `imu_link`：IMU 坐标系。
- `left_wheel_link`、`right_wheel_link`：左右轮。
- `caster_link`：万向轮。

当前 URDF 主要用于外形显示和静态 TF，没有完整的碰撞体、惯性、Gazebo 传感器和差速驱动插件，所以还不能直接作为物理仿真模型。

### 4.3 `xuegecar_bringup`：基础节点与 TF

```text
xuegecar_bringup/
├── src/
│   └── xuegecar_bringup.cpp
├── launch/
│   └── xuegecar_bringup.launch.py
├── CMakeLists.txt
└── package.xml
```

`xuegecar_bringup.cpp`：

- 创建 `xuegecar_bringup` 节点。
- 订阅 `/odom`。
- 将里程计位姿转换为 `odom -> base_footprint` TF。

`xuegecar_bringup.launch.py` 同时启动：

- `joint_state_publisher`
- `robot_state_publisher`
- `xuegecar_bringup`

### 4.4 `leap_interfaces`：自定义服务接口

```text 
leap_interfaces/
├── srv/
│   ├── GetSpeedPid.srv
│   └── SetSpeedPid.srv
├── CMakeLists.txt
└── package.xml
```

服务定义只规定请求和响应的数据结构，不包含 PID 算法。对应服务为：

- `/get_speed_pid`
- `/set_speed_pid`

### 4.5 `xuegecar_mavlink_bridge`：MAVLink 桥

```text
xuegecar_mavlink_bridge/
├── include/                   # 桥接节点头文件及 MAVLink 协议头
├── src/                       # 串口/UDP、协议解析和 ROS 节点实现
├── config/
│   └── mavlink_bridge.yaml    # 端口、波特率、话题等参数
├── launch/
│   └── mavlink_bridge.launch.py
├── CMakeLists.txt
└── package.xml
```

它位于 ROS 2 与 ESP32 之间：

```text
ROS /cmd_vel → MAVLink → ESP32
ESP32 传感器数据 → MAVLink → ROS /odom、/imu、/scan 等
```

阅读时先看 YAML 和 launch，再找节点构造函数、发布者、订阅者和 MAVLink 消息分支。

### 4.6 `camsense_lidar`：雷达驱动

```text
camsense_lidar/
├── include/camsense_lidar/    # 雷达解析类声明
├── src/
│   ├── camsense_lidar.cpp     # 雷达协议和数据解析
│   └── camsense_lidar_node.cpp# ROS 2 节点入口
├── launch/
│   └── camsense_lidar.launch.py
├── params/
│   └── camsense_lidar.yaml
├── CMakeLists.txt
├── package.xml
└── README.md
```

主要任务是打开串口、解析扫描数据并发布 `/scan`。根目录中还存在旧版 `camsense_lidar.cpp/.h`，阅读时优先以 `src/`、`include/` 和当前 CMake 编译规则为准。

### 4.7 `xuegecar_camera`：HTTP 视频节点

```text
xuegecar_camera/
├── xuegecar_camera/
│   ├── __init__.py
│   └── http_video_publisher.py
├── config/
│   └── http_video_publisher.yaml
├── launch/
│   └── http_video_publisher.launch.py
├── resource/
├── setup.py
├── setup.cfg
├── package.xml
└── README.md
```

这是 Python 功能包。`http_video_publisher.py` 才是节点源代码，它读取 ESP32 摄像头的 HTTP/MJPEG 流，发布压缩图像，并可选发布原始图像。

### 4.8 `openslam_gmapping` 与 `slam_gmapping`：GMapping

```text
openslam_gmapping/             # 粒子滤波、栅格、扫描匹配等底层算法
slam_gmapping/
├── include/slam_gmapping/     # ROS 封装头文件
├── src/                       # ROS 节点实现
├── launch/
│   └── slam_gmapping.launch.py
├── params/
│   └── slam_gmapping.yaml
├── CMakeLists.txt
└── package.xml
```

二者关系为：

```text
/scan + TF/odom
       ↓
slam_gmapping（ROS 2 封装）
       ↓
openslam_gmapping（算法库）
       ↓
/map + map→odom TF
```

初学时先看 `slam_gmapping` 的 launch 和参数，不必立刻深入 `openslam_gmapping` 的算法源码。

### 4.9 `xuegecar_cartographer`：另一套建图方案

```text
xuegecar_cartographer/
├── config/                    # Cartographer Lua 配置
├── launch/
│   └── cartographer.launch.py
├── CMakeLists.txt
└── package.xml
```

启动 Cartographer 节点、栅格地图节点和 RViz。它与 GMapping 是两种可选建图方案，通常不应同时负责发布同一套地图和 TF。

### 4.10 `xuegecar_navigation2`：Nav2 导航

```text
xuegecar_navigation2/
├── launch/
│   ├── navigation2.launch.py       # 仅启动 Nav2
│   ├── navigation2_rviz.launch.py  # Nav2 + RViz
│   └── slam_nav2.launch.py         # GMapping + Nav2 + RViz
├── param/
│   ├── nav2.yaml
│   └── xuegebot.yaml
├── config/
│   └── ekf.yaml
├── maps/
│   ├── room.yaml 及对应图片
│   └── 其他预制地图
├── CMakeLists.txt
└── package.xml
```

这里主要是启动和参数配置，不是 Nav2 核心算法源码。它配置地图服务器、定位、规划器、控制器、行为树、代价地图及传感器融合等组件。

### 4.11 `xuegecar_qt_gui`：主控制界面

```text
xuegecar_qt_gui/
├── include/                   # 界面类和 ROS 数据接口声明
├── src/                       # Qt 窗口、绘图、ROS 通信实现
├── launch/
│   └── xuegecar_qt_gui.launch.py
├── CMakeLists.txt
├── package.xml
└── README.md
```

主要功能：

- 订阅地图、雷达、里程计、路径、摄像头和电池数据。
- 发布 `/cmd_vel`、导航目标和初始位姿。
- 显示机器人位置、轨迹和导航状态。
- 从界面启动或停止部分 ROS 进程。

### 4.12 `xuegecar_servo_qt_gui`：舵机调试界面

```text
xuegecar_servo_qt_gui/
├── include/
├── src/
├── launch/
│   └── xuegecar_servo_qt_gui.launch.py
├── CMakeLists.txt
├── package.xml
└── README.md
```

用于通过 `/servo_cmd` 发布舵机控制数据，与主界面分开，便于单独调试执行器。

## 5. ESP32-S3 底盘固件结构

```text
leap_ros_mcu_driver/
├── main/                  # 本项目自己编写的主要业务代码
│   ├── app_main.cpp       # ESP-IDF 程序总入口
│   ├── app_runtime.*      # 初始化和任务启动组织
│   ├── platform/
│   │   └── board.*        # GPIO、UART、I2C、ADC 等板级定义
│   ├── core/
│   │   └── system_globals.* # 全局状态、队列和运行配置
│   ├── config/
│   │   └── pid_config.*   # PID 参数存储和加载
│   ├── control/
│   │   └── motion_controller.* # 差速运动学、PID、里程计
│   ├── network/
│   │   └── wifi_app.*     # Wi-Fi 初始化和连接
│   ├── msg/               # FreeRTOS 任务间传递的数据结构
│   └── tasks/
│       ├── control/       # 运动控制任务
│       ├── sensors/       # IMU、雷达、超声波、电池任务
│       ├── network/       # micro-ROS、MAVLink 通信任务
│       └── io/            # 舵机、灯、按键、摄像头等外围任务
├── components/            # 可复用硬件驱动组件
│   ├── motor_driver/
│   ├── encoder_driver/
│   ├── pid_controller/
│   ├── lsm6ds3_driver/
│   ├── camsense_lidar/
│   ├── ultrasonic_sensor/
│   ├── battery_adc/
│   ├── servo_driver/
│   ├── camera_i2c_client/
│   ├── status_led/
│   └── ws2812_driver/
├── extra_ros_packages/    # micro-ROS 构建所需自定义 ROS 接口副本
├── managed_components/    # ESP-IDF 管理的第三方组件
├── doc/
│   └── protocols.md       # 通信协议说明
├── CMakeLists.txt
├── sdkconfig              # ESP-IDF 工程配置结果
└── partitions.csv         # Flash 分区表（如存在）
```

### 5.1 `main` 和 `components` 的区别

- `main`：组合各模块，形成这辆小车的完整业务逻辑。
- `components`：封装某一种硬件或通用能力，可被 `main` 调用。
- `managed_components`：外部依赖，初学和业务修改阶段通常不用阅读。

### 5.2 底盘程序主要调用关系

```text
app_main.cpp
    ↓
app_runtime.cpp
    ├── 初始化 board、Wi-Fi 和配置
    ├── 创建任务间队列
    ├── 启动 motion/IMU/lidar/battery 等任务
    └── 根据配置启动 micro-ROS 或 MAVLink
             ↓
       motion_controller
             ↓
 motor_driver + encoder_driver + pid_controller
```

### 5.3 `msg` 目录的含义

底盘 `main/msg/*.h` 不是 ROS 2 的 `msg` 接口包，而主要是 ESP32 内部任务间通过 FreeRTOS 队列交换的数据结构，例如：

- `motion_msg.h`
- `imu_msg.h`
- `lidar_msg.h`
- `battery_msg.h`
- `servo_msg.h`
- `ultrasonic_msg.h`

不要将它与 ROS 工作区中通过 `rosidl` 生成的 ROS 消息混为一谈。

## 6. ESP32 摄像头固件结构

```text
leap_cam/
├── main/
│   ├── camera_init.c          # 摄像头型号、引脚和图像参数
│   ├── web_mjpeg.c            # HTTP/MJPEG 视频流服务
│   ├── web_config.c           # Web 配网页面和配置接口
│   ├── i2c_slave_comm.c       # 与底盘 MCU 的 I2C 从机通信
│   ├── board_control.c        # 板级控制
│   ├── wifi_manager.c         # Wi-Fi 管理
│   └── 其他启动和发现服务代码
├── components/                # 摄像头及网络相关组件
├── managed_components/        # ESP-IDF 管理的第三方组件
├── CMakeLists.txt
└── sdkconfig
```

它本身不是 ROS 2 节点。图像链路是：

```text
摄像头传感器
   ↓
leap_cam 输出 HTTP/MJPEG
   ↓
xuegecar_camera/http_video_publisher.py
   ↓
/camera/image_raw/compressed
   ↓
Qt GUI 或其他 ROS 图像节点
```

## 7. 三部分如何连接

### 7.1 控制链路

```text
Qt GUI / Nav2 / 键盘
          ↓ 发布
       /cmd_vel
          ↓
micro-ROS 或 xuegecar_mavlink_bridge
          ↓
ESP32 motion_controller
          ↓
左右轮目标速度 → PID → 电机驱动
```

### 7.2 里程计与导航链路

```text
编码器
  ↓
ESP32 运动学积分
  ↓
/odom
  ├──→ xuegecar_bringup → odom→base_footprint TF
  ├──→ SLAM
  ├──→ Nav2
  └──→ Qt GUI
```

### 7.3 雷达建图链路

```text
雷达 → /scan + TF + /odom
                 ↓
       GMapping 或 Cartographer
                 ↓
                /map
                 ↓
        Nav2 / RViz / Qt GUI
```

### 7.4 导航闭环

```text
用户发布 /goal_pose
          ↓
Nav2 根据 /map、/scan、TF 规划和避障
          ↓
Nav2 发布 /cmd_vel
          ↓
底盘运动并重新发布 /odom、/scan
```

## 8. 阅读代码的推荐顺序

### 第一阶段：先建立全局概念

1. `xuegeros_demo/launch/bringup_all.launch.py`
2. `xuegecar_bringup/launch/xuegecar_bringup.launch.py`
3. `xuegecar_description/urdf/xuegecar.urdf`
4. 各包的 `package.xml` 和 `CMakeLists.txt`/`setup.py`

目标：知道有哪些进程、模型和依赖。

### 第二阶段：理解一条完整控制链

1. Qt 界面或 Nav2 如何发布 `/cmd_vel`。
2. `microros_task.cpp` 或 MAVLink 桥如何接收命令。
3. `motion_controller.cpp` 如何算左右轮目标值。
4. `motor_driver`、`encoder_driver` 和 `pid_controller` 如何闭环。
5. 编码器如何形成 `/odom`。

### 第三阶段：理解感知和建图

1. 雷达如何形成 `/scan`。
2. URDF 如何提供 `base_link -> laser_frame`。
3. GMapping/Cartographer 如何使用 `/scan` 和 TF。
4. 地图如何提供给 Nav2 和界面。

### 第四阶段：理解上层功能

1. Nav2 参数和启动文件。
2. Qt GUI 的订阅、发布和绘图代码。
3. 摄像头固件与 ROS 图像节点。

### 第五阶段：再看细节和第三方算法

最后再深入 OpenSLAM、MAVLink 自动生成头文件和 `managed_components`。这些代码量很大，但不是理解项目主流程的第一入口。

## 9. 快速判断一个文件的作用

看到陌生功能包时，可按此顺序检查：

1. 看 `package.xml`：它依赖什么、属于 C++ 还是 Python 包。
2. 看 `CMakeLists.txt` 或 `setup.py`：哪些源文件真正被编译，生成什么可执行节点。
3. 看 `launch`：作者打算启动哪些节点、传入什么参数。
4. 看 `config/param`：节点的重要可调参数。
5. 看 `include`：类和接口结构。
6. 看 `src`：具体实现、发布者、订阅者、服务、定时器和算法。

寻找 ROS 2 节点核心逻辑时，重点搜索：

```text
rclcpp::Node / Node(...)
create_publisher
create_subscription
create_service
create_client
create_wall_timer
declare_parameter
get_parameter
```

Python 节点则重点搜索：

```text
class ... (Node)
create_publisher
create_subscription
create_service
create_timer
declare_parameter
```

## 10. 当前尚缺的仿真结构

当前目录里没有完整的 `xuegecar_sim` 功能包。后续建议新增：

```text
xuegecar_sim/
├── urdf/
│   └── xuegecar_sim.urdf.xacro
├── worlds/
│   └── test_room.sdf
├── config/
│   └── controllers.yaml
├── launch/
│   └── simulation.launch.py
├── CMakeLists.txt
└── package.xml
```

仿真层应模拟真实底盘相同的上层接口：

```text
/cmd_vel  /odom  /scan  /imu  /clock 以及完整 TF
```

这样 SLAM、Nav2 和 Qt GUI 可以在真实模式与仿真模式之间复用，而不必修改上层业务代码。

## 11. 一句话记忆

```text
include 定义接口，src 实现功能，config 保存参数，launch 负责组织启动；
ROS 2 工作区负责上层，leap_ros_mcu_driver 负责底盘，leap_cam 负责视频。
```
