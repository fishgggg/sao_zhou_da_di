# ROS2 小车 · 仿真搭建教学（从零到最小闭环，再叠回真实能力）

> **定位**：从空白文件夹出发，搭建 XuegeCar 的 Gazebo 仿真系统。全程只定「命名对象与结构」（包名 / 节点 / 话题 / 服务 / TF / 参数 / 图 / 表），不写实现代码。
> **节奏**：一次一阶段 → 学生复述 → 确认 → 下一阶段。
> **产物**：本文档按阶段增量追加，可逐步回看修订。
> **对照源（只读，阶段 11 才扫描）**：`C:\Users\Y\Desktop\ros_car\xuegeros_ws\xuegeros_ws\src`、`C:\Users\Y\Desktop\ros_car\leap_demo`

---

## 〇 · 全局路线图（骨架）

```
幕一 · 打地基（阶段 0-2）    纸面工作，零代码：先把「接口 / 坐标 / 职责」钉死
        │                    —— ROS2 小车翻车，九成不是文件少，是契约没定
        ▼
幕二 · 最小闭环（阶段 3-5）  第一次让轮子转起来、第一次拿到传感器数据
        │                    —— 没有这条闭环，后面一切都在流沙上盖楼
        ▼
幕三 · 叠能力（阶段 6-10）   建图 → 导航 → 任务层 → 启动 → 测试
        │                    —— 此时改任何一层，底层都已「可验证」
        ▼
收束（阶段 11）             回 C 盘扫真实代码，出「实际架构快照」+ 差异表
```

| 阶段 | 一句话目标 | 阶段末可自查的验证标志 |
|---|---|---|
| 0 | 环境搭建 + 项目契约 | 一句话说得清任务；4 条版本命令全绿 |
| 1 | 架构与数据流：冻结接口 | 一张节点图 + 一棵 TF 树 + 一张接口表 |
| 2 | 包结构与依赖 | 依赖树无环，只有 2 个最小包 |
| 3 ★ | 最小闭环：遥控→cmd_vel→差速插件→轮子→odom→TF→RViz | RViz 里小车按键盘动、odom 稳、tf 无报错 |
| 4 | 机器人描述工程化（xacro / 惯量 / 碰撞 / 材质） | 模型不乱飘、关节可控 |
| 5 | 传感器接入（scan / imu / battery / ultrasonic） | 频率稳、时间戳顺、TF 对 |
| 6 | 建图与定位（GMapping + AMCL） | map 成形，map→odom→base_footprint 完整 |
| 7 | 导航栈（Nav2） | 发目标点能走、能避障、能恢复 |
| 8 | 应用层与任务状态机 | 状态切换清晰，急停随时生效 |
| 9 | 启动 / 参数 / 命名空间 | 一条 launch 拉起全系统，use_sim_time 正确 |
| 10 | 测试、调试与回归 | 每次改动能回归（含 WSL2 特有项） |
| 11 | 与现有代码对照 | 9 项交付物齐全，差异表可解释 |

**两个教学机关（刻意设计，不是遗漏）**：

1. 阶段 3 与阶段 4 看着重复，实为 **「最小够用」→「工程化补全」** 的递进：阶段 3 的 URDF 只补到「能进 Gazebo 物理运动」；阶段 4 才回头做参数化与精修。**先跑通再精修。**
2. 从零设计期间 **刻意不读 C 盘实现细节**（只认接口清单），阶段 11 的差异对照才有意义，否则等于照着答案抄。

---

## 〇 · 前置决策（已确认）

| # | 决策点 | 结论 |
|---|---|---|
| 1 | 设计产物留存 | 本文档，按阶段增量追加 |
| 2 | 环境现状 | WSL2 尚未安装 → 阶段 0 从「装环境」讲起 |
| 3 | 物理参数（轮径 / 轮距 / 车体尺寸） | 先用典型值打样，阶段 11 对着实车校准 |

---

## 〇 · 附：ROS2 项目的标准开发工作流（心法）

**装好软件 ≠ 会做项目**，中间隔着一条「工程流程」。成熟工程师的顺序：

| 步 | 做什么 | 对应本课 |
|---|---|---|
| 1 | **定契约**：要什么、怎么算成功 | 阶段 0 |
| 2 | **定接口**：谁跟谁说话、说什么、在哪说 | 阶段 1 |
| 3 | **立骨架**：先把空包 / 目录立起来，不求能跑 | 阶段 2 |
| 4 | **最小可运行单元**：一次只让一个东西跑起来 | 阶段 3 |
| 5 | **逐条接线**：一次接一条链路，接完立刻验证 | 阶段 3-5 |
| 6 | **叠能力**：在已验证的地基上继续加 | 阶段 6-10 |
| 7 | **对照校准**：回真实项目比对 | 阶段 11 |

**贯穿全程的三条心法**：

1. **永远让系统保持「能跑」** —— 不留半成品状态。宁可功能少，不可系统坏。
2. **一次只加一个东西** —— 同时改两处，出问题就无法二分定位。
3. **加完立刻验证** —— 没有验证的改动等于没做（绿非证明，复现即证）。

> 新手与熟手最大的分野就在这里：新手想一次做全（完整 URDF + 传感器 + SLAM + Nav2 一起上），熟手的第一个目标是 **让一辆最简陋的车先动起来**。

---

## 阶段 0 · 环境搭建与项目契约

### 本步目标

得到两样东西：
1. 一个 **能启动 Gazebo、能跑 ros2 命令、能弹出 GUI** 的 WSL2 环境（**可运行的物理事实**）；
2. 一张 **项目契约卡**（**纸面共识**）——把「小车在什么环境、完成什么任务、边界在哪」提前钉死。

### 为什么现在做这一步

不是「先随便建个包试试」。ROS2 小车的失败模式里，最常见的是：**文件都写了，但接口对不上、坐标错位、频率乱、职责重叠**。契约把这些「看不见的约定」提前固化，后面每一步设计都有依据。

至于为什么「环境」和「契约」绑在一个阶段：**契约里写的『环境』必须有物理落点**。你环境是空的，所以本阶段的「环境确认」必须升级为「环境搭建」——装完再回头验证契约里那句环境描述成立，逻辑才闭环。

### 前置输入

- 硬件：一台 Windows 主机（WSL2 宿主），无实车。
- 已知：ROS2 Humble / Ubuntu 22.04 / Gazebo Classic 11 的技术选型已定。
- 待定：物理参数用典型值（见前置决策 3）。

---

### 0.1 环境搭建

#### 组件清单与「为什么需要它」

| 组件 | 装什么 | 为什么需要 |
|---|---|---|
| 运行环境 | WSL2 + Ubuntu 22.04 (jammy) | ROS2 Humble 的官方支持平台 |
| GUI 通道 | WSLg | 让 rviz2 / gzclient 的窗口显示到 Windows |
| ROS2 | `ros-humble-desktop` | 含 rclcpp / rclpy / rviz2 / demo |
| 仿真器 | Gazebo Classic 11 | 物理引擎 + 传感器模拟 |
| 桥接 | `ros-humble-gazebo-ros-pkgs` | 让 Gazebo 与 ROS2 互认（**含差速插件 gazebo_ros_diff_drive**） |
| 建模 | `ros-humble-xacro` | URDF 参数化 |
| 遥控 | `ros-humble-teleop-twist-keyboard` | 发 `/cmd_vel` |
| 关节状态 | `ros-humble-joint-state-publisher`(+gui) | 差速轮关节状态发布 |
| 构建 | `colcon` / `rosdep` | 建包 / 装依赖 |

#### 安装次序（命令供参考，源配置以官网为准）

1. **Windows 侧**（PowerShell）：`wsl --install -d Ubuntu-22.04`，随后 `wsl --update`（拿 WSLg）。
2. **ROS 2 Humble**：按官网 Humble Debian 安装页配置 apt 源，核心一步 `sudo apt install ros-humble-desktop`，并把 `source /opt/ros/humble/setup.bash` 写进 `~/.bashrc`。
3. **Gazebo Classic 11**：加 OSRF 源后 `sudo apt install gazebo`（官方 `classic.gazebosim.org` 安装页的 standard 方式）。
4. **桥与工具**：`sudo apt install ros-humble-gazebo-ros-pkgs ros-humble-xacro ros-humble-teleop-twist-keyboard ros-humble-robot-state-publisher ros-humble-joint-state-publisher ros-humble-joint-state-publisher-gui`。

> 依据：Gazebo 官方教程 *Installing gazebo_ros_pkgs (ROS 2)* 明确 `sudo apt install ros-<distro>-gazebo-ros-pkgs`（Humble 即替换为 `ros-humble-...`），并随包安装官方 demo 世界于 `/opt/ros/<distro>/share/gazebo_plugins/worlds/`。

#### WSL2 特有的坑（本阶段重点）

| 坑 | 现象 | 处理 |
|---|---|---|
| WSLg 不生效 | rviz2 报 `cannot connect to display` | 需 Win11 22H2+ 且 `wsl --update`；验证 `echo $DISPLAY`（约 `:0`）与 `ls /mnt/wslg` |
| Gazebo 黑屏 / 崩 | gzclient 起不来 | WSL2 默认无 GPU 直通 → 退软件渲染 `LIBGL_ALWAYS_SOFTWARE=1`；慢但稳 |
| 时钟漂移 | WSL 休眠后 DDS 时间乱、TF 报「future」 | `sudo hwclock -s` 或 `wsl --shutdown` 重启 |
| Gazebo Classic 已 EOL | 官方 2025-01 停止支持 | Humble 官方搭配仍是它，WSL2 下比 Gazebo Sim 稳 —— 继续用，只是知道它到站了 |

#### 验证方式（自己动手跑）

```
echo $ROS_DISTRO          → humble
gzserver --version        → 11.x
gzclient --version        → 11.x
ros2 pkg list | grep gazebo   → gazebo_ros / gazebo_plugins
ros2 pkg list | grep xacro    → xacro
rviz2                     → 弹出窗口
```
**加分验证**（提前偷看阶段 3 的终点）：`gazebo --verbose /opt/ros/humble/share/gazebo_plugins/worlds/gazebo_ros_diff_drive_demo.world` 应出现一辆小车，再 `ros2 topic pub /demo/cmd_demo geometry_msgs/Twist '{linear: {x: 1.0}}' -1` 它应前行。**这一步跑通，说明「Gazebo + diff_drive 插件」整条链已就绪。**

---

### 0.2 项目契约卡

#### 八要素

| 要素 | 内容 |
|---|---|
| **任务（一句话）** | 一辆差速驱动小车，在室内平面环境中接收速度指令并运动，同时发布里程计与传感器数据，作为后续建图 / 导航的载体。 |
| **环境** | WSL2 / Ubuntu 22.04 / ROS2 Humble / Gazebo Classic 11 / 默认 DDS / `use_sim_time=true` |
| **硬件边界** | 无实车。ESP32 底盘 → 由 `gazebo_ros_diff_drive` 插件替代；真实传感器 → 由 Gazebo 插件替代。 |
| **通信边界** | 仅 ROS2 话题 / 服务（DDS）。micro-ROS / MAVLink 属实车侧，仿真不引入。 |
| **成功标准** | 阶段 3 末：RViz 中小车响应 `/cmd_vel` 移动，`/odom` 连续稳定，TF 树完整且无报错。 |
| **风险** | ① WSLg 渲染 ② Gazebo Classic EOL ③ 时钟漂移 ④ 轮径/轮距为典型值（待校准） |
| **假设** | ① 单机单机器人 ② 键盘遥控 ③ 第一版不用 ros2_control ④ 不涉及多机 DDS 发现 |
| **非目标** | 本期不做实车部署、不做 Nav2 精细调参、不做多传感器融合 |

#### 命名对象（阶段 0 产出）

- **任务名**：最小仿真闭环（标识暂定 `xuegecar_sim`）
- **场景名**：`empty_world`（阶段 3 落地）
- **成功指标**：见上「成功标准」
- **约束 / 假设 / 风险**：见上表

#### 验证方式

你能用**一句话**说清「小车在什么环境完成什么任务」（即复述上面「任务」那一格）。

---

### 常见错误

- 只装 ROS2 没装 `gazebo_ros_pkgs` → 后面找不到 `gazebo_ros` / 差速插件，阶段 3 直接卡死。
- 用 Gazebo Sim（Ignition）的插件名（`gz_ros2_*`）配 Classic → 插件加载失败。**本课全程 Classic，只认 `libgazebo_ros_*`**。
- 契约里的「成功标准」写成「能跑起来」这类**不可验证**的话 → 阶段 3 无法判定是否完成。

### 下一步

**阶段 1 · 系统架构与数据流**：把节点、话题、服务、动作、参数、TF 树、QoS、频率全部冻结成一张图 + 一组表。因为 ROS2 是分布式数据流系统——**先定接口，再写实现**。

### 学情记录（阶段 0）

- **已完成**：WSL2 + ROS2 Humble + `gazebo_ros_pkgs` 安装完成；Gazebo 图形界面可打开；helloworld 跑通。
- **已完成（补记）**：ROS2 ↔ Gazebo 链路已验证——官方差速 demo 世界跑通、小车响应 `/cmd_vel`；契约卡已过目认可。**阶段 0 闭环**（契约未强制口头复述，教法已转示范式）。
- **卡点**：学生无法用一句话说出「小车在什么环境完成什么任务」。
- **根因**：此前学习方式为「逐行注释 + 看 AI 解释」，属**自下而上的实现层学习**，缺少**自上而下的系统 / 流程视角**。这不是知识缺口，是**方法论缺口**。
- **教学调整**：由「提问—等待复述」改为「教师示范成熟工程师的思路 + 学生跟随执行」，保留动手验证，降低纯复述压力。

### 学生提问（待复述）

见对话区（阶段 0 后半已转为示范式教学）。


---

## 阶段 1 · 系统架构与数据流

### 本步目标

把整个系统的「接口」冻结成三样可检查的产物：**一张节点图 + 一棵 TF 树 + 一组接口表**。

### 为什么现在做这一步

ROS2 的本质是「分布式数据流系统」：节点之间**不直接互相调用**，而是通过话题 / 服务**广播—订阅**。所以系统的真身就是一张数据流图。

比喻：**定接口 = 画电路图；写代码 = 焊电路。没人先焊再想电路图。**

反过来更致命：如果先写节点、再定话题名，改一个名字就要改所有引用它的节点——牵一发动全身。所以**接口必须先冻结**。

### 前置输入

- 阶段 0 的契约卡（任务 / 环境 / 边界 / 成功标准）。
- 已知的真实项目接口清单（话题名 / 服务名 / TF frame），见前置信息。

---

### 创建的命名对象

#### A. 节点（最小闭环 5 个）

| 节点 | 角色 | 启用阶段 |
|---|---|---|
| `teleop_twist_keyboard` | 遥控：键盘 → `/cmd_vel` | 3 |
| `gazebo`（内含 `gazebo_ros_diff_drive` 插件） | 仿真物理 + 差速控制 + 里程计（= 仿真世界里的「底盘」） | 3 |
| `robot_state_publisher` | 读 URDF，发布连杆 TF | 3 |
| `joint_state_publisher`（仿真中可由 Gazebo 的关节状态插件替代） | 发布轮子关节角 → 给 RSP | 3 |
| `rviz2` | 可视化（订阅 TF / odom） | 3 |

后续：`slam_gmapping` / `cartographer`（阶段 6）、Nav2 各 server（阶段 7）、Qt GUI（阶段 8）。

#### B. 节点连接图（最小闭环）

```text
  [teleop_twist_keyboard]
            │ /cmd_vel  (geometry_msgs/Twist)
            ▼
  ┌──────────────────────────────────┐
  │            Gazebo 11             │
  │   gazebo_ros_diff_drive 插件     │
  │  （仿真世界里的「底盘」）          │
  └──────────────────────────────────┘
            │ /odom  (nav_msgs/Odometry)
            │ /tf    odom → base_footprint
            │ /clock (rosgraph_msgs/Clock)
            ▼
  [robot_state_publisher] ◀── /joint_states ── [joint_state_publisher]
            │ /tf   base_footprint → base_link → …
            ▼
         [rviz2]
```

#### C. TF 树（坐标系）

```text
odom                        ← 里程计原点（漂移参考系）
 └─ base_footprint          ← 车体在地面的投影
     └─ base_link           ← 车体主体
         ├─ laser_frame
         ├─ imu_link
         ├─ ultrasonic_link
         ├─ left_wheel_link
         ├─ right_wheel_link
         └─ caster_link
```

**谁发布哪一段**（关键）：

| TF 边 | 发布者 | 说明 |
|---|---|---|
| `odom → base_footprint` | `gazebo_ros_diff_drive` 插件 | 由 `publish_odom_tf` 参数控制 |
| `base_footprint → base_link → 各连杆` | `robot_state_publisher` | 读 URDF + `/joint_states` |
| `map → odom` | SLAM / AMCL | 阶段 6 才出现 |

> **铁律：同一条 TF 边只能有一个发布者。** 两个节点同时发 `odom → base_footprint`，TF 树会打架——真实项目文档里已点名这个风险。

#### D. 话题表

| 话题 | 消息类型 | 发布者 | 订阅者 | 建议频率 | 引入阶段 |
|---|---|---|---|---|---|
| `/clock` | rosgraph_msgs/Clock | Gazebo | 所有节点 | — | 3 |
| `/cmd_vel` | geometry_msgs/Twist | teleop / Nav2 | diff_drive 插件 | 事件驱动 | 3 |
| `/odom` | nav_msgs/Odometry | diff_drive 插件 | RViz / SLAM / Nav2 | ~50 Hz | 3 |
| `/joint_states` | sensor_msgs/JointState | joint_state_publisher | RSP | 10 Hz | 3 |
| `/tf`、`/tf_static` | tf2_msgs/TFMessage | RSP / 插件 | 全体 | — | 3 |
| `/scan` | sensor_msgs/LaserScan | 雷达插件 | SLAM / Nav2 / RViz | 10 Hz | 5 |
| `/imu` | sensor_msgs/Imu | IMU 插件 | EKF / Nav2 | 50 Hz | 5 |
| `/battery_state` | sensor_msgs/BatteryState | 电池插件 | Qt GUI | 1 Hz | 5 |
| `/ultrasonic` | sensor_msgs/Range | 超声波插件 | Qt GUI | 10 Hz | 5 |
| `/camera/image_raw/compressed` | sensor_msgs/CompressedImage | 摄像头节点 | Qt GUI | ~30 Hz | 5+ |
| `/map` | nav_msgs/OccupancyGrid | SLAM / map_server | Nav2 / RViz | 1 Hz | 6 |
| `/initialpose` | geometry_msgs/PoseWithCovarianceStamped | RViz / Qt GUI | AMCL | 事件驱动 | 6 |
| `/goal_pose` | geometry_msgs/PoseStamped | RViz / Qt GUI | Nav2 | 事件驱动 | 7 |

#### E. 服务与动作

| 名称 | 类型 | 提供者 | 消费者 | 仿真侧 |
|---|---|---|---|---|
| `/set_speed_pid` | leap_interfaces/SetSpeedPid | ESP32 底盘（实车） | Qt GUI | ❌ **仿真不存在** |
| `/get_speed_pid` | leap_interfaces/GetSpeedPid | ESP32 底盘（实车） | Qt GUI | ❌ **仿真不存在** |
| `/navigate_to_pose` | nav2_msgs/action/NavigateToPose | bt_navigator | RViz / Qt | 阶段 7 |

> **重要差异点**：PID 服务是**实车独有**的——PID 闭环跑在 ESP32 上，经 micro-ROS / MAVLink 暴露给上位机。仿真里速度闭环由 Gazebo 物理隐式完成，**没有这个服务**。这是阶段 11「仿真↔固件差异表」的第一条。

#### F. 参数（第一批）

| 参数 | 归属 | 含义 |
|---|---|---|
| `use_sim_time` | 所有节点 | 仿真中必须 `true`，否则时间戳错乱 |
| `left_joint` / `right_joint` | diff_drive 插件 | 左右轮关节名 |
| `wheel_separation` | diff_drive 插件 | 轮距（暂用典型值） |
| `wheel_diameter` | diff_drive 插件 | 轮径（暂用典型值） |
| `max_wheel_torque` | diff_drive 插件 | 力矩上限 |
| `max_wheel_acceleration` | diff_drive 插件 | 加速度上限 |
| `publish_odom` | diff_drive 插件 | 是否发布 `/odom` |
| `publish_odom_tf` | diff_drive 插件 | 是否发布 `odom → base_footprint` TF |
| `odom_frame` / `base_frame` | diff_drive 插件 | 里程计 / 车体 frame 名 |

#### G. QoS（服务质量）

| 话题 | QoS 档 | 理由 |
|---|---|---|
| `/cmd_vel` | Reliable, depth 10 | 控制指令不能丢 |
| `/odom` | Reliable | 里程计供 SLAM / Nav2 消费 |
| `/scan`、`/imu` | **BestEffort**（SensorDataQoS） | 高频传感器流，丢帧可容忍 |
| `/tf` | 默认 | — |

> **新手最常踩的坑**：发布方 Reliable、订阅方 BestEffort（或反之）→ **订阅端收不到任何数据，而且不报错**。ROS2 不会帮你警告。

---

### 嵌套关系

节点图 ⊃ 每个节点的「发布 / 订阅」定义；TF 树 ⊃ 每一条父子边；接口表 ⊃ 每个话题的「类型 + 两端 + 频率 + QoS」。

### 连接关系

见 B（节点图）与 C（TF 树）。一句话：**`/cmd_vel` 进、`/odom` 出、`/tf` 把坐标串成一棵树。**

### 验证方式

阶段 1 是纯设计，**本阶段不会产生自己的话题**。真正的验证落在阶段 3 搭完之后——不过现在就有捷径：

> **你刚跑通的官方 `gazebo_ros_diff_drive_demo.world` 就是一份活的教材**，它此刻正在跑一张迷你节点图。用它当「标本」，把上面的图对照成实物：
>
> ```
> ros2 topic list                 # 看到 /demo/cmd_demo、/demo/odom 等
> ros2 node list                  # 看到 gazebo 侧节点
> rqt_graph                       # 看到节点连线（最直观）
> ros2 run tf2_tools view_frames  # 生成 frames.pdf，看 demo 的 TF 树
> ros2 topic hz /demo/odom        # 看它真实频率
> ```
>
> **这是整门课最重要的习惯**：设计出来的图，永远要找一个能跑的实物去对照。另外注意——demo 里那辆车是 Gazebo 自带的示例模型，**不是你的车**；它跑通只证明「链路通」，不代表「你的小车搭好了」。

阶段 3 搭完后的正式验证：

| 检查 | 命令 | 期望 |
|---|---|---|
| 话题都在 | `ros2 topic list` | 见 `/cmd_vel` `/odom` `/clock` `/joint_states` |
| 频率对 | `ros2 topic hz /odom` | 约 50 Hz |
| TF 树完整 | `ros2 run tf2_tools view_frames` | 生成 frames.pdf，树形正确 |
| 节点连上了 | `rqt_graph` | teleop → 插件 → RSP 连线可见 |
| 时钟在走 | `ros2 topic hz /clock` | 有频率（证明 use_sim_time 生效） |

### 常见错误

- 同一条 TF 边有两个发布者 → TF 树打架、RViz 抖动。
- frame 名拼写不一致（`base_footprint` vs `base_footprint `）→ 树断开。
- QoS 档不匹配 → 订阅端静默收不到数据。
- 忘了 `/clock` 或没开 `use_sim_time` → 时间戳全是 0，报 `extrapolation into the future`。

### 补充：话题的「方向」怎么看（由学生提问引发）

`ros2 topic list` **只报告「有哪些频道名」，不报告方向**——方向由「节点对话题做了什么」决定，不是话题自身的属性。

| 命令 | 能看到什么 |
|---|---|
| `ros2 topic list` | 有哪些话题（**无方向**） |
| `ros2 topic info /x` | 该话题的发布者数 / 订阅者数 |
| `ros2 topic info /x -v` | 具体是哪些节点在发 / 收 |
| `ros2 node info /节点` | 该节点发什么、收什么（**方向最清楚**） |
| `rqt_graph` | 图形化（最直观） |
| `ros2 topic echo /x` | 数据确实在流（但看不出谁发） |

**认知升级：话题是「频道」（多对多），不是「管道」（一对一）。**

- 同一话题可以有 0 个或多个发布者、多个订阅者；
- 「方向」不是话题的属性，而是「某个节点对该话题 publish 还是 subscribe」的属性；
- **话题是动态的**：节点一退出，话题就消失（ROS2 动态发现）。

**基础设施话题**：任何有节点活着的 ROS2 系统里，都会有 `/rosout`（日志）和 `/parameter_events`（参数事件）。若只看得到这两个，说明**系统里没有业务节点在跑**。

**关于 `/cmd_vel`**：它不是 ROS2 内置话题，而是**社区约定俗成的名字**（command velocity），类型 `geometry_msgs/msg/Twist`（线速度 + 角速度六分量）。`ros2 topic list` 里找不到它，只因为**此刻没有节点在发布 / 订阅它**，不代表它「不存在」。

### 工程习惯：参数语义以 `--help` 为准

`ros2 topic pub` 的 `-1/--once`、`-r/--rate`、`-t/--times` 各有明确语义，**不要凭记忆**：

```
ros2 topic pub --help
```

> **文档、教程、甚至 AI 都可能记错——`--help` 与实测输出才是最终裁判。**
> （另：`geometry_msgs/msg/Twist` 与 `geometry_msgs/Twist` 两种类型写法 CLI 都接受。）

### 实测记录：官方 demo 的真实数据流（阶段 1 现场）

**节点未启动时**（对照基线）：
```
/parameter_events
/rosout
```

**Gazebo demo 世界启动后**：
```
$ ros2 topic list
/clock
/demo/cmd_demo
/demo/odom_demo
/parameter_events
/rosout
/tf
```
→ **话题是从无到有「长出来」的**，坐实「话题是动态的」。

```
$ ros2 topic info /demo/cmd_demo -v
Type: geometry_msgs/msg/Twist
Publisher count: 0
Subscription count: 1
  Node name: diff_drive
  Node namespace: /demo
  Endpoint type: SUBSCRIPTION
  QoS: Reliability = RELIABLE, Durability = VOLATILE
```

**`Publisher count: 0` 是全场重点**：此刻没人在发，但有一个人在听——**话题照样存在**。这直接证明：话题是「频道」，其存在由任一端点（发布者或订阅者）维持，**方向不属于话题本身**。

```
$ ros2 node list
/demo/diff_drive
```
注意：**gzserver 本身不在 ROS 图里**——Gazebo 只是「宿主」，真正注册为 ROS 节点的是**插件**（`diff_drive`）。

| 阶段 1 设计图 | demo 实测 | 说明 |
|---|---|---|
| `/cmd_vel` | `/demo/cmd_demo` | 控制输入；发布者要自己提供（teleop 或 `ros2 topic pub`） |
| `/odom` | `/demo/odom_demo` | 里程计输出 |
| `/clock` | `/clock` | **仿真特有**：Gazebo 发布的虚拟时钟，实车不存在 |
| `/tf` | `/tf` | 坐标变换 |
| `teleop_twist_keyboard` | （无） | demo 没有遥控节点，需手动发指令 |
| `gazebo_ros_diff_drive` 插件 | `/demo/diff_drive` 节点 | 底盘 |

> **结论：名字不同，结构完全相同。** 看懂这一点，就拿到了读任何陌生 ROS2 项目的钥匙。

### 下一步

**阶段 2 · 包结构与依赖**：接口定了，该决定「这些节点 / 文件放在哪些包里、包之间谁依赖谁」。原则：按职责分层，**避免循环依赖**，也避免「一个包塞所有东西」。

### 学生提问（待复述）

见对话区。

### 现场排障：终端 ≠ 进程（本课第一次系统故障）

**事件**：直接点终端窗口的「叉号」关闭，没能正常关掉 Gazebo，随后启动报错。

**根因认知**：**终端只是「窗口 / 显示器」，进程是独立的生命。**

- 关窗口 **≠** 杀进程。前台进程可能收到 SIGHUP 而被终止，但**子进程（`gzserver` / `gzclient`）常常变成孤儿进程继续跑**，或以半死状态残留（占用端口、锁文件）。
- 正确关闭方式：
  - 前台运行中 → 在终端里按 `Ctrl-C`
  - 已成孤儿 / 后台 → `killall gzserver gzclient`
  - 先查再杀 → `ps aux | grep -E "gzserver|gzclient"`

**三层排查法（从下往上）**：

| 层 | 查什么 | 命令 |
|---|---|---|
| 进程层 | Gazebo 进程在不在 | `ps aux \| grep -E "gzserver\|gzclient"` |
| 节点层 | ROS 节点在不在 | `ros2 node list` |
| 话题层 | 话题在不在 | `ros2 topic list` |

**哪一层先空，问题就在那一层。** 这是排查「系统没起来」的通用顺序。

> 教训：**跑通一次** 和 **能稳定复现** 之间，隔着一层「进程管理」的基本功。
> 另：`ros2 topic pub` 参数已由学生实测确认——`-r/--rate` 默认 1 Hz，即**不带 `-1` 时是持续发布**，而非「只发一次」（教师原说法已纠正）。

**重启 Gazebo 报错速查（通用）**：

| 现象（大致） | 可能原因 | 对策 |
|---|---|---|
| 启动即退出；提示锁 / 共享内存 / server 已存在 | 上次进程未清干净，残留锁文件或共享内存 | `killall gzserver gzclient`；仍不行 → `wsl --shutdown` 后重开 WSL |
| 启动卡住不动 | 旧 `gzserver` 还占着资源 | `ps aux \| grep gzserver` 找到后 `kill -9 <PID>` |
| `cannot connect to display` | WSLg / DISPLAY 问题 | 检查 `echo $DISPLAY`；`wsl --update`；重启 WSL |
| 有物理无窗口 | `gzclient` 未起来或渲染失败 | 单独跑 `LIBGL_ALWAYS_SOFTWARE=1 gzclient` |

> 通用原则：**先看进程层，再看节点层，最后看话题层。** 报错原文永远比猜测值钱。

**实测取证**（在 Windows 侧执行 `wsl -e bash -c "ps aux | grep gazebo"`）：

```
y  1071  18.5%  SLl  19:19  3:00  gzserver --verbose .../gazebo_ros_diff_drive_demo.world
```

结论：**关窗口后 `gzclient`（GUI）死了，`gzserver`（物理引擎）活了下来**，继续占用 `11345` 端口 → 新启动被拒（`Address already in use`）。

补救：`kill 1071`（或 `killall gzserver`）→ 用 `ps aux | grep gzserver` 确认清空 → 重启 Gazebo。

---

## 阶段 2 · 包结构与依赖

### 本步目标

决定「这些节点 / 文件放进哪些包、包之间谁依赖谁」。产出：**一张包依赖树 + 两个最小包的定义**。

### 为什么现在做这一步

阶段 1 冻结了**接口**，阶段 2 给每个接口找**住所**。两条原则：

1. **按职责分层**——而不是「一个大包塞所有东西」。
2. **依赖必须单向**——形成无环的依赖树。

反例：一个包塞所有东西 → 只想做仿真，却要连带编译 SLAM、Nav2、Qt GUI；改一行、全量重编。

### 前置输入

阶段 1 的节点图 / TF 树 / 接口表。

---

### 创建的命名对象

#### 工作空间

```
xuegecar_sim_ws/            ← 从零新建的仿真工作空间（与真实项目 xuegeros_ws 并列、互不干扰）
└── src/
    ├── xuegecar_sim_description/
    └── xuegecar_sim_bringup/
```

#### 包 1：`xuegecar_sim_description`（描述包）

职责：**只放「机器人长什么样」**，不放任何逻辑。

```
xuegecar_sim_description/
├── urdf/xuegecar_sim.urdf.xacro
├── meshes/
├── rviz/
├── package.xml
└── CMakeLists.txt
```

#### 包 2：`xuegecar_sim_bringup`（仿真启动包）

职责：**只放「怎么把机器人放进仿真世界并跑起来」**。

```
xuegecar_sim_bringup/
├── launch/gazebo.launch.py
├── config/
├── worlds/
├── package.xml
└── CMakeLists.txt
```

#### 依赖方向（单向、无环）

```
xuegecar_sim_bringup  ──▶  xuegecar_sim_description
```

bringup 依赖 description（要加载 URDF）；**description 绝不依赖 bringup**。

#### 为什么是 2 个包，不是一个？

- **职责不同**：一个是「模型」，一个是「编排」。
- **复用**：模型会被多种场景复用（RViz 看模型、仿真、将来的实车 bringup），而启动编排各不相同。
- **成本**：包不是越多越好——每多一个包 = 多一份 `package.xml` / 构建脚本 / 依赖管理。**只有职责足够独立时才分包。**

#### 为什么新建 `xuegecar_sim_description`，不复用现有 `xuegecar_description`？

| 方案 | 优点 | 缺点 |
|---|---|---|
| **新建 sim_description** | 不污染现有包；两份 URDF 可做差异对照（阶段 11 的教学素材）；仿真要求 collision / inertial / 插件，与原「仅供显示」的 URDF 差异很大 | 两份 URDF 可能漂移 |
| 复用 xuegecar_description | 单一真相源 | 要改动现有包；原 URDF 不能直接用于物理仿真 |

**本课选「新建」**——因为目标是「从零搭一遍」，最后再做差异对照。

### 嵌套关系

工作空间 ⊃ 包 ⊃ 目录（`urdf/` `launch/` …）⊃ 文件。

### 连接关系

包之间唯一的连接是**依赖声明**（`package.xml`），方向单一：bringup → description。

### 验证方式

| 检查 | 命令 | 期望 |
|---|---|---|
| 两个包都被识别 | `ros2 pkg list \| grep xuegecar_sim` | 两行 |
| 包能被定位 | `ros2 pkg prefix xuegecar_sim_description` | 输出 install 路径 |
| 依赖无环 | 检查两个 `package.xml` | 单向链 |
| 能构建 | `colcon build` | 成功 |

### 常见错误

- **循环依赖**：A 依赖 B、B 又依赖 A → 构建失败或行为诡异。
- **包名与节点名混用**：包名是「仓库单位」，节点名是「运行时单位」，两者不同。
- **什么都塞一个包** → 依赖爆棚、编译慢、无法复用。

### 下一步

**阶段 3 · 最小闭环**：骨架立好，真正让轮子转起来。

### 学生提问（待复述）

见对话区。

---

## 阶段 3 · 仿真最小闭环（核心阶段）

### 本步目标

**让轮子第一次转起来。** 打通：遥控 → `/cmd_vel` → 差速插件 → 轮子关节 → `/odom` → TF → RViz。

### 为什么现在做这一步

- 这是整门课**第一个能"看见"的里程碑**：屏幕里一辆小车，按键盘它就走。
- 在此之前所有东西都在纸上；**从这里开始，图纸变成文件**。
- 不先打通这条最底层的闭环，后面的 SLAM / Nav2 / Qt GUI **统统无法脱离实车调试**。

### 前置输入

- 阶段 1 接口表（`/cmd_vel` `/odom` `/joint_states` `/clock` `/tf`）
- 阶段 2 包结构（`description` + `bringup`）
- 代码位置：`~/xuegecar_sim_ws/`（**WSL 原生文件系统，不放 `/mnt/c`**，否则 `colcon build` 慢数倍）

---

### 〇、拆成三小步（每步都能独立验证）

| 小步 | 做什么 | 独立验证 |
|---|---|---|
| **3.1** | 建两个**空包**（只有 `package.xml` + `CMakeLists.txt`） | `colcon build` 通过；`ros2 pkg list` 看得到 |
| **3.2** | 写 **URDF**（纯模型，先不挂插件） | `robot_state_publisher` + RViz 里看到一辆静止的小车 |
| **3.3** | 挂 **diff_drive 插件** + 写 launch + 遥控 | 车能动能转，`/odom` 有数据，TF 树完整 |

> 这就是「最小可运行单元 → 逐条接线」心法的实操：**每加一样东西，立刻验证一次。**

### 一、施工清单（要建的文件）

```
~/xuegecar_sim_ws/
└── src/
    ├── xuegecar_sim_description/
    │   ├── urdf/xuegecar_sim.urdf        ← 机器人模型 + Gazebo 差速插件
    │   ├── meshes/                       ← 阶段 3 留空（用基本几何体）
    │   ├── rviz/sim.rviz                 ← 可选
    │   ├── package.xml
    │   └── CMakeLists.txt
    └── xuegecar_sim_bringup/
        ├── launch/gazebo.launch.py       ← 起 gazebo + RSP + spawn
        ├── config/                       ← 阶段 3 可空
        ├── package.xml
        └── CMakeLists.txt
```

> 阶段 3 用**纯 URDF**（`xuegecar_sim.urdf`），阶段 4 才转 xacro 参数化——**先跑通，再精修**。

### 二、URDF 骨架（结构说明，非代码）

**link 清单（5 个）**：

| link | 角色 | 需要 collision? |
|---|---|---|
| `base_footprint` | 地面投影（虚拟点） | ❌ **不要** |
| `base_link` | 车体主体 | ✅ |
| `left_wheel_link` | 左轮 | ✅ |
| `right_wheel_link` | 右轮 | ✅ |
| `caster_link` | 万向轮 | ✅ |

**joint 清单（4 个）**：

| joint | 连接 | 类型 | 关键 |
|---|---|---|---|
| `base_joint` | base_footprint → base_link | `fixed` | — |
| `left_wheel_joint` | base_link → left_wheel_link | **`continuous`** | ⚠️ 必须能无限旋转 |
| `right_wheel_joint` | base_link → right_wheel_link | **`continuous`** | ⚠️ 同上 |
| `caster_joint` | base_link → caster_link | `continuous` / `fixed` | 见「常见错误」 |

**每个实体 link 的三件套**（新手最容易漏）：

| 元素 | 作用 | 漏了会怎样 |
|---|---|---|
| `visual` | 看得见 | 模型透明 |
| `collision` | 碰得到 | **穿地、穿墙** |
| `inertial` | 质量 / 惯量 | Gazebo 警告，物理行为飘忽 |

**打样用的典型值**（阶段 11 对着实车校准）：

| 量 | 值 |
|---|---|
| 车体尺寸 | 0.20 × 0.15 × 0.08 m |
| 轮半径 | 0.0325 m |
| 轮宽 | 0.02 m |
| 轮距（左右轮心距） | 0.17 m |
| 车体质量 | ~1.0 kg |
| 单轮质量 | ~0.1 kg |

### 三、Gazebo 差速插件（本阶段的心脏）

在 URDF 里挂 `libgazebo_ros_diff_drive.so`——**它就是仿真世界里的 ESP32 底盘**。

| 参数 | 含义 |
|---|---|
| `left_joint` / `right_joint` | 左右轮关节名 |
| `wheel_separation` | 轮距 |
| `wheel_diameter` | 轮径 |
| `max_wheel_torque` | 力矩上限 |
| `max_wheel_acceleration` | 加速度上限 |
| `publish_odom` | 是否发 `/odom` |
| `publish_odom_tf` | 是否发 `odom → base_footprint` TF |
| `odom_frame` / `base_frame` | frame 名 |

> 它一个人干三件事：**收 `/cmd_vel`、算差速运动学、发 `/odom` + TF**。

### 四、launch 干三件事

`gazebo.launch.py` 负责按顺序：

1. 启动 **Gazebo**（物理世界）
2. 启动 **`robot_state_publisher`**（读 URDF，发连杆 TF）
3. 启动 **`spawn_entity`**（把机器人放进世界）

⚠️ **顺序有讲究**：模型必须等 Gazebo 起来后再 spawn，否则丢进虚空。

### 五、验证（逐级递进）

| # | 命令 | 期望 |
|---|---|---|
| 1 | `ros2 launch xuegecar_sim_bringup gazebo.launch.py` | Gazebo 里出现小车 |
| 2 | `ros2 topic list` | 见 `/cmd_vel` `/odom` `/joint_states` `/clock` `/tf` |
| 3 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` | 按键 → **车动** |
| 4 | `ros2 run tf2_tools view_frames` | TF 树完整、无断链 |
| 5 | `ros2 topic hz /odom` | 有稳定频率 |

### 六、常见错误（按踩中概率排序）

| 现象 | 根因 |
|---|---|
| 车纹丝不动 | 轮子 joint 用了 `revolute` / `fixed`，不是 `continuous` |
| 车原地打转 / 走歪 | 左右轮**轴向**反了，或 `wheel_separation` 填错 |
| 车穿过地面或墙 | `collision` 缺失 |
| Gazebo 警告 inertial、车体抖动发飘 | `inertial` 缺失或数值离谱 |
| 模型掉进虚空 | `spawn_entity` 比 Gazebo 起得早 |
| `base_footprint` 与地面打架 | 给它加了 `collision`（它是虚拟点） |
| TF 报 `extrapolation into the future` | 没开 `use_sim_time` |

### 七、下一步

**阶段 4 · 机器人描述工程化**：把"能跑的 URDF"升级为参数化 xacro——**为什么需要它，那时的痛点会自己冒出来**。

### 学生提问（待复述）

见对话区。

### 补充：仿真与实车的边界（学生提问引发）

**分层看，边界只有一层**：

```
   应用层     Qt GUI / Nav2 / SLAM               ← 仿真 & 实车 完全相同
      ↕
   接口层     /cmd_vel /odom /scan /tf           ← 完全相同（这就是「契约」的价值）
      ↕
   ┌──────────────┬──────────────────┐
   │    实车侧     │      仿真侧       │        ← 只有这一层不同
   │ MAVLink 桥    │  diff_drive 插件  │
   │ ESP32 固件    │  Gazebo 物理      │
   │ 电机 / 编码器 │  虚拟关节 / 碰撞  │
   └──────────────┴──────────────────┘
```

#### Q1：URDF 只有仿真项目才写吗？

**不是。URDF 是通用资产**——实车项目同样需要它，因为：

- RViz 要显示机器人模型；
- `base_link → laser_frame` 等**静态 TF** 要靠 `robot_state_publisher` 从 URDF 发布；
- Nav2 / SLAM 依赖完整的 TF 树。

**但 URDF 的内容分两类**：

| URDF 内容 | 实车 | 仿真 |
|---|---|---|
| link / joint 层级（TF 树） | ✅ 必用 | ✅ 必用 |
| visual | ✅ RViz 显示 | ✅ |
| collision | ❌ 真车自己就会碰 | ✅ **物理碰撞必需** |
| inertial | ❌ 真车有真实质量 | ✅ **物理仿真必需** |
| **Gazebo 插件 / `<gazebo>` 标签** | ❌ **完全不用** | ✅ **核心** |

> **重要纠正**：现有项目的 `xuegecar.urdf` 缺 collision / inertial / 插件——**这不是缺陷**，而是**它只服务实车**，尚无仿真需求。

#### Q2：「操作小车」在实车和仿真里有什么区别？

**上层一字不改，只换最下面一层。**

| 层面 | 实车 | 仿真 |
|---|---|---|
| 谁接收 `/cmd_vel` | ESP32（经 MAVLink / micro-ROS） | `diff_drive` 插件 |
| 运动学计算 | ESP32 固件 | 插件 |
| 电机驱动 | 真实 PWM | Gazebo 物理 |
| 里程计来源 | 编码器 → 固件积分 | Gazebo 物理积分 |
| teleop / RViz / Nav2 | **完全相同** | **完全相同** |

**判断口诀**：问自己「这东西是**描述**机器人，还是**驱动 / 模拟**机器人？」

- 描述（URDF 的 TF 部分）→ 两边都要
- 模拟物理（collision / inertial / 插件）→ 仿真专用
- 驱动硬件（固件 / 电机 / 编码器）→ 实车专用

> **局限提醒**：仿真是理想世界——无噪声、无延迟、不打滑。**仿真跑通 ≠ 实车能跑通。**

### 3.1 实测：`colcon build` 成功了，为什么 `ros2 pkg list` 看不到？

**实测输出**：
```
$ colcon build
Summary: 2 packages finished [2.14s]      ← 构建成功

$ ros2 pkg list | grep xuegecar_sim       ← 空！一行都没有
```

**根因：构建成功 ≠ 包可见。中间隔着一次 `source`。**

ROS2 的环境是**叠加（overlay）**的：

```
/opt/ros/humble/                 ← underlay（系统安装的底座）
        +
~/xuegecar_sim_ws/install/       ← overlay（你新建的这一层）
        ↓
   source install/setup.bash 之后，两层合并
        ↓
   ros2 pkg list 才能看得到你的包
```

`colcon build` 只是把包**安装到** `install/` 目录；`ros2` 命令**并不认识它**，直到你把这个目录 **source 进当前终端的环境变量**（本质是往 `AMENT_PREFIX_PATH` / `PATH` 里加路径）。

**解决**：

```bash
source ~/xuegecar_sim_ws/install/setup.bash
ros2 pkg list | grep xuegecar_sim     # 现在应看到两行
```

**验证安装位置**：

```bash
ros2 pkg prefix xuegecar_sim_description
# → ~/xuegecar_sim_ws/install/xuegecar_sim_description
```

**每次改代码后的固定动作**：`colcon build` → **重开终端或重新 source**。

> 类比（给有 MCU 背景的人）：这就像 `make` 出了固件却没烧进芯片——文件在磁盘上躺着，但"运行环境"还不知道它的存在。`source` = 烧录 + 重启。

### 3.2 URDF 脚手架（全阶段最容易翻车的一步）

**目标**：RViz 里看到一辆**静止**的小车。**先不挂任何插件**——把「模型对不对」和「物理能不能跑」**分开验证**。

**文件**：`~/xuegecar_sim_ws/src/xuegecar_sim_description/urdf/xuegecar_sim.urdf`

#### 层级与坐标（一个自洽的方案）

```
base_footprint            ← z = 0（地面投影，虚拟点）
   │ base_joint [fixed]，z 偏移 = +0.0325（= 轮半径）
   ▼
base_link                 ← 位于「轮心高度」
   ├─ left_wheel_joint  [continuous]，origin (0, +0.085, 0)，axis (0,1,0)
   ├─ right_wheel_joint [continuous]，origin (0, -0.085, 0)，axis (0,1,0)
   └─ caster_joint      [continuous]，origin (-0.07, 0, -0.0175)
```

> 设计要点：把 `base_link` 放在**轮心高度**（= 轮半径），于是轮心相对 `base_link` 的 z 偏移正好为 0——坐标最干净。

#### 每个 link 要什么

| link | visual | collision | inertial |
|---|---|---|---|
| `base_footprint` | ❌ 不写 | ❌ **不写** | ❌ 不写 |
| `base_link` | ✅ box 0.20×0.15×0.08，z=+0.04 | ✅ 同 visual | ✅ 质量 1.0 kg |
| `left_wheel_link` | ✅ cylinder r=0.0325、长 0.02，**rpy 绕 x 转 90°** | ✅ 同 visual | ✅ 质量 0.1 kg |
| `right_wheel_link` | 同上 | 同上 | 同上 |
| `caster_link` | ✅ sphere r=0.015 | ✅ 同 visual | ✅ 质量 0.05 kg |

#### 三个最容易翻车的点

1. **轮子 joint 必须 `continuous`**——`revolute` 是「有角度上限」、`fixed` 是「焊死」，两者都会让车不动。
2. **`<cylinder>` 默认沿 z 轴**——车轮是躺在 y 方向的，所以 `visual` / `collision` 的 `origin rpy` 要绕 x 转 90°（约 `1.5708 0 0`）。否则轮子会像「立着的硬币」。
3. **`base_footprint` 绝不能有 `collision`**——它是虚拟的地面投影点；给它碰撞体会和地面打架，车会乱跳。

#### 验证（暂不涉及 Gazebo）

```bash
cd ~/xuegecar_sim_ws/src/xuegecar_sim_description/urdf
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat xuegecar_sim.urdf)" -p use_sim_time:=false
```

另开终端：

```bash
rviz2      # 左侧 Add → RobotModel；Fixed Frame 设为 base_footprint
```

**判据**：RViz 里出现一辆**静止的小车**——轮子在两侧，车体在上方。
若解析失败，`robot_state_publisher` 会直接打印报错（很多情况下带有问题的行号）——**照着改**。

#### 常见错误

| 现象 | 根因 |
|---|---|
| RSP 启动即报错 | URDF 语法错（标签未闭合、属性名拼错、数值分隔符用了逗号） |
| RViz 看不到模型 | 没设 Fixed Frame，或 `robot_description` 参数为空 |
| 模型「零件分离」 | joint 的 `origin` 算错 |
| 轮子竖着像硬币 | cylinder 没转 90° |

#### 小教训（3.1 实测中发现）

学生把 `echo "source ..." >> ~/.bashrc` **执行了两次**，导致 `~/.bashrc` 里出现两行重复。
`>>` 是**追加**，重复执行就会重复写入。修正：

```bash
sed -i '\|xuegecar_sim_ws/install/setup.bash|d' ~/.bashrc   # 先删干净
echo "source ~/xuegecar_sim_ws/install/setup.bash" >> ~/.bashrc
```

### 教学分工约定（学生提问澄清）

**问**：URDF 的层级与坐标方案，是老师写还是学生写？

**答**：

- **设计归老师**：层级、坐标、数值、为什么——已完成（见上）。
- **URDF 文件归学生**：把它翻译成 XML 语法。
- **老师不给完整文件**——这是学生自己定的规则（不输出完整 URDF / launch 文件）。

**为什么这么分**：

- 本课目标是**「理解设计」**，不是**「拿到成品」**。
- 「写」这一步会**暴露理解缺口**——对不上的地方，正是学习发生的地方。
- 数值是**可以被质疑**的：轮距为什么 0.17？`base_link` 为什么放在轮心高度？这些是设计决策，学生可以推翻并给出自己的理由。

**老师提供的弹药**：

1. 设计（层级 / 坐标 / 数值表）；
2. 语法参照：ROS 2 官方 URDF 教程；以及现有项目 `xuegecar.urdf`（**只看语法写法，不看设计取舍**）；
3. 卡住随时问——给「片段级提示」，不给完整文件。

**预判会卡住的地方**：

- XML 语法本身（标签闭合、属性引号、数值**用空格分隔、不能用逗号**）；
- `inertial` 的惯量矩阵；
- `cylinder` 的 90° 旋转。

**常用惯量公式**（实心体，绕自身质心）：

| 形状 | Ixx | Iyy | Izz |
|---|---|---|---|
| 长方体 (x×y×z) | m(y²+z²)/12 | m(x²+z²)/12 | m(x²+y²)/12 |
| 圆柱（轴沿 z，半径 r，高 h） | m(3r²+h²)/12 | m(3r²+h²)/12 | m·r²/2 |
| 球（半径 r） | 2mr²/5 | 2mr²/5 | 2mr²/5 |

> 注：URDF 的惯量是在**自身 link 坐标系**下给出的；若 link 的几何有旋转，惯量矩阵原则上要随之变换——**打样阶段可以先填近似值**，阶段 4 再精算。

### 教学分工约定（修订）

**规则变更**：原「不输出完整代码 / URDF / launch」条款**作废**。

**变更原因**：学生从「只想看流程」转为「要实际复现」，无法自行手写全套代码。

**新分工**：

- **老师写代码**——可直接写入学生的 WSL 工程目录（省去手抄）。
- **写一步、讲一步**：每步都要说明「现在要干什么 / 判断标准是什么」。
- **一次只加一个东西**：每步都能独立验证。
- 学生负责：跑验证、看结果、提问题。

**长期目标**：让学生学会「**如何指挥 AI 做工程 + 验证 AI 的产出**」——这比手写 XML 更有价值。

**技术备忘**：跨 Windows→WSL 写文件的通路
`write_file` 写到 Windows 侧 → `wsl -e bash -c "cp /mnt/c/... /home/y/..."` → `sed -i "s/\r$//"` 去 CRLF。

### 技巧：如何快速验证一段 URDF（本轮实测）

**问题**：`robot_state_publisher` 是**常驻节点**，启动后不会自己退出——怎么在一条命令里验证它「能不能正常启动」？

**答案**：用 `timeout` 包一层。

```bash
wsl -e bash -c 'source /opt/ros/humble/setup.bash; timeout 6 ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(cat /path/to/xuegecar_sim.urdf)" 2>&1 | head -40'
```

**判读表**：

| 输出 | 含义 |
|---|---|
| `got segment base_footprint` / `got segment base_link` | ✅ 解析成功，URDF 有效 |
| 报错并退出 | ❌ URDF 语法问题（通常带行号） |
| 无输出但没退出 | 进程活着，其实也是成功 |
| exit=124 | `timeout` 正常终止（**不是错误**） |

**通用模式**：想验证一个**常驻进程**能否正常启动 → `timeout N <命令>`，看启动阶段有没有报错。

这正是「**绿非证明，复现即证**」的实操——不猜，让工具自己说话。

**附带发现**：`xacro` **未安装**（阶段 4 需要，届时 `sudo apt install ros-humble-xacro`）。

### 案例：AI 写错了配置，学生抓到了（3.2-a 收官）

**事件链**：

1. 老师写 `.rviz` 配置时，**凭记忆**填了插件类名 `tf2_ros/TransformListener`——**未经核实**。
2. 学生运行后 RViz 报错：
   ```
   PluginlibFactory: The plugin for class 'tf2_ros/TransformListener' failed to load.
   ... Declared types are  rviz_default_plugins/TF
   ```
   ——**报错文本自己给出了正确答案**。
3. 修复：删除该段（RViz 自动使用默认的 TF）。
4. 老师做**系统性排雷**：把 `.rviz` 里用到的每个 Class 与 RViz 插件注册表逐个对照 → **8/8 显示插件类全部 OK**。
5. 但面板类 `rviz_common/Displays` / `rviz_common/Views` 报 MISSING——**与实际现象矛盾**（面板明明在工作）。
6. 追查：它们在 `share/rviz_common/` 下**没有插件注册 XML**——属于 **RViz 内置类**，不走插件注册表。交叉验证：官方 `default.rviz` 用了同样的类名 → **合法**。

**三条可复用教训**：

1. **AI 的产出必须验证**——它会凭记忆写出不存在的类名 / API / 参数。
2. **报错文本常常直接给出答案**（`Declared types are ...` 就是正确值）。
3. **验证方法本身也可能有盲区**——当「检查结果」与「实际现象」矛盾时，先怀疑检查方法，别急着下结论。

### 3.2-b 装上轮子（附一个必须知道的机制）

**新增**：2 个 wheel link + 2 个 `continuous` 关节。

#### 关键决策逐条

| 决策 | 值 | 为什么 |
|---|---|---|
| 轮子位置 y | `±0.085` | = 轮距 0.17 的一半；REP-103 约定 **y 向左为正** |
| 轮子位置 z | `0` | **因为 a 步已把 base_link 抬到轮心高度**——a 步埋的伏笔在此回收 |
| 轮子位置 x | `0` | 轮子在车体中间 |
| cylinder 姿态 | `rpy="1.5708 0 0"` | URDF 的 cylinder 默认轴沿 z（立着）；车轮要轴沿 y（躺下） |
| joint 类型 | `continuous` | 无限旋转 |
| joint axis | `(0,1,0)` | 绕 y 轴转 |
| 惯量 Iyy | `m·r²/2` | 绕圆柱轴（y）的公式；Ixx = Izz 用 `m(3r²+h²)/12` |

#### ⚠️ 必须知道的机制：fixed 与 movable 关节的 TF 发布方式不同

**实测证据**（b 步 URDF 写入后只跑 RSP）：

```
A. 解析出的 link：base_footprint / base_link / left_wheel_link / right_wheel_link
B. /tf_static：只有 base_footprint → base_link        ← 轮子不在里面！
C. 只有 RSP 时 /tf：空
```

**原因**：

| 关节类型 | RSP 怎么发 TF |
|---|---|
| `fixed` | 位置永远不变 → 直接算出来发到 `/tf_static`（发一次，永久有效） |
| `continuous` / `revolute` / `prismatic` | **角度随时在变** → 必须先知道「当前角度」→ 从 `/joint_states` 读 → **没人发，就没有 TF** |

**所以需要一个节点**：`joint_state_publisher`
→ 读 URDF，为所有可动关节发布默认角度（全 0）到 `/joint_states`。

> **回扣阶段 1**：节点图里那个 `joint_state_publisher` 方框，当时只是纸上一个名字；
> 现在亲眼看到——**没有它，轮子在 RViz 里根本不会出现**。

**本机额外发现**：`joint_state_publisher` **未安装**，需要
`sudo apt install ros-humble-joint-state-publisher ros-humble-joint-state-publisher-gui`
（`sudo` 需要密码，AI 代不了）。

#### 启动方式（3 个终端）

```bash
# 终端 1：RSP（发 TF 骨架）
ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p robot_description:="$(cat ~/xuegecar_sim_ws/src/xuegecar_sim_description/urdf/xuegecar_sim.urdf)" \
             -p use_sim_time:=false

# 终端 2：关节状态（发 /joint_states，让轮子 TF 出现）
ros2 run joint_state_publisher joint_state_publisher \
  --ros-args -p robot_description:="$(cat ~/xuegecar_sim_ws/src/xuegecar_sim_description/urdf/xuegecar_sim.urdf)"

# 终端 3：RViz
rviz2 -d ~/xuegecar_sim_ws/src/xuegecar_sim_description/rviz/xuegecar_sim.rviz
```

#### 判据

RViz 里应看到：**蓝色方块 + 两侧各一个黑色圆柱**，且**轮子底部正好落在地面网格上**。

### 3.2-c + 3.3：万向轮 与「让车动起来」

#### c 步：caster 为什么必须有

差速小车只有两个**驱动轮**着地 → 前后方向没有支撑 → 在 Gazebo 里会「点头」甚至翻倒。
caster（万向轮）提供**第三点支撑**，把两点支撑变成三点支撑。

```
       俯视
   ┌─────────────┐
   │   base_link │
   │ ○         ○ │   ← 左右驱动轮（y = ±0.085）
   │             │
   │      ●      │   ← caster（x = -0.07，车尾）
   └─────────────┘
```

**位置计算**：球半径 0.015，要接触地面 → 球心离地 0.015；
相对 base_link（已在 0.0325 高度）→ `0.015 - 0.0325 = -0.0175`。

**摩擦必须设 0**：`<gazebo reference="caster_link"><mu1>0</mu1><mu2>0</mu2></gazebo>`
否则这个球会「拖住」小车，车跑不动或跑歪。

#### 3.3：两个插件，两条闭环

```
[teleop_twist_keyboard]
        │ /cmd_vel
        ▼
[gazebo_ros_diff_drive 插件]  ← 仿真世界里的「底盘」
        ├─ 驱动 left / right_wheel_joint（物理）
        ├─ 发 /odom
        └─ 发 TF：odom → base_footprint
        ▼
[gazebo_ros_joint_state_publisher 插件]
        │ /joint_states（轮子的真实转角）
        ▼
[robot_state_publisher]
        ├─ /tf：base_link → left/right_wheel_link
        └─ /tf_static：base_footprint → base_link
```

> **TF 的分工**：`odom→base_footprint` 由**插件**发（它知道车走到哪了）；
> `base_link→wheel` 由 **RSP** 发（它读 URDF + joint_states）。**两条线，互不重叠。**

#### launch 按顺序做三件事

| # | 做什么 | 为什么 |
|---|---|---|
| 1 | 启动 Gazebo | 物理世界 |
| 2 | 启动 robot_state_publisher | 读 URDF、发 TF，**并把 URDF 发到 `/robot_description` 话题** |
| 3 | 延迟 5 秒后 spawn_entity | 从 `/robot_description` 话题读模型放进 Gazebo；**必须等 Gazebo 服务就绪**，否则掉进虚空 |

#### 实测验证记录（AI 代跑，`gui:=false` 无头模式）

| 检查 | 结果 |
|---|---|
| spawn | `Successfully spawned entity [xuegecar_sim]` |
| 话题 | `/clock` `/cmd_vel` `/joint_states` `/odom` `/robot_description` `/tf` `/tf_static` |
| 节点 | `/diff_drive` `/gazebo` `/robot_state_publisher` |
| `/joint_states` | left / right / caster 三个关节都有 position 数据 |
| `/tf_static` | `base_footprint → base_link` |
| `/tf` | `odom → base_footprint`，以及 `left_wheel_link` / `right_wheel_link` / `caster_link` |
| `/odom` | `frame_id: odom`、`child_frame_id: base_footprint`，有数据 |
| 日志错误 | 无 |

#### ⚠️ WSL2 的一个坑：DDS 发现慢（重要）

测量 `/odom` 时曾出现 `topic [/odom] does not appear to be published yet`，
但**实际是有数据的**——换个更长的采样窗口就收到了。

**原因**：WSL2 下 ROS2 的节点发现（DDS discovery）比原生 Linux 慢，
`ros2 topic hz` / `echo` 的默认采样窗口可能不够。

**结论**：**在 WSL2 里做验证，给足时间（10 秒以上）；
别把「一时没收到」直接判成「没有数据」——多测一次，换长时间版本。**

#### 关键命令差异（与 a/b 步对比）

| 阶段 | 启动方式 |
|---|---|
| a / b 步 | 手动分开跑 `robot_state_publisher`（+ `joint_state_publisher`）+ `rviz2` |
| **3.3** | **一条 launch 全搞定**：`ros2 launch xuegecar_sim_bringup gazebo.launch.py` |
