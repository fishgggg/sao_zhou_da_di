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

### 答疑：信息都放在哪？（阶段 3 收官问答）

学生问：「小车的配件信息就是放在 `gazebo_ros_diff_drive` 里？它的初始放置坐标、旋转关系、连接程度，这些都存放在哪？」

**答：不是。`gazebo_ros_diff_drive` 只存「怎么驱动」，配件信息全在 URDF。**

| 你想知道的 | 它在哪 |
|---|---|
| 部件形状（车体 / 轮子） | URDF 的 `<visual>` / `<geometry>` |
| 部件**位置** | URDF 的 `<origin xyz="...">` |
| 部件**朝向 / 旋转** | URDF 的 `<origin rpy="...">` |
| 部件之间**怎么连接** | URDF 的 `<joint type="fixed / continuous / ...">` |
| 归属关系（谁是父） | URDF 的 `<parent>` / `<child>` |
| 质量、惯量 | URDF 的 `<inertial>` |
| **谁驱动轮子、怎么算 odom** | `gazebo_ros_diff_drive` 插件（**只做这件事**） |
| **轮子转角从哪来** | `gazebo_ros_joint_state_publisher` 插件 |
| **小车初始放在世界哪里** | ⚠️ **不在 URDF**——在 launch 的 `spawn_entity -z 0.05` |
| 启动顺序 | launch 文件 |
| RViz 显示什么 | `.rviz` 文件 |

#### 一个措辞纠正

`teleop_twist_keyboard` 是**发布者**（发 `/cmd_vel`）；
`gazebo_ros_diff_drive` 是**订阅者**（收 `/cmd_vel`）。
**没有谁在「订阅 teleop」**——两者通过**话题**间接连接，互不认识。

#### 我们一共建了什么（实测清单）

7 个文件，共 479 行：

| 文件 | 行数 | 性质 |
|---|---|---|
| `xuegecar_sim_description/urdf/xuegecar_sim.urdf` | 216 | **内容：描述小车** |
| `xuegecar_sim_bringup/launch/gazebo.launch.py` | 86 | **内容：组织启动** |
| `xuegecar_sim_description/rviz/xuegecar_sim.rviz` | 96 | **内容：显示配置** |
| `xuegecar_sim_description/CMakeLists.txt` | 23 | 样板：安装规则 |
| `xuegecar_sim_bringup/CMakeLists.txt` | 22 | 样板：安装规则 |
| `xuegecar_sim_description/package.xml` | 18 | 样板：包身份证 |
| `xuegecar_sim_bringup/package.xml` | 18 | 样板：包身份证 |

#### 为什么「感觉东西太少」是个正确的直觉

对比手写 STM32 小车：

| STM32 上要手写 | ROS2 仿真里 |
|---|---|
| GPIO / 定时器 / 中断初始化 | ❌ 框架负责 |
| 编码器读取 | ❌ 插件负责 |
| PID 闭环 | ❌ Gazebo 物理引擎 |
| 运动学解算（差速） | ❌ diff_drive 插件 |
| 串口 / 通信协议 | ❌ DDS 负责 |
| 可视化 | ❌ RViz 负责 |

**你写的：479 行。背后在跑的：Gazebo + ROS2，千万行量级。**

> **这既是 ROS 的价值，也是它反直觉的地方：ROS2 项目的主体是「声明 + 接线」，不是「写算法」。**
> 你从「什么都自己写」的 MCU 世界，跳到了「框架提供底座、你只搭结构」的世界。

#### 但确实还缺东西（诚实的差距清单）

- 传感器：`/scan` `/imu` `/battery_state` `/ultrasonic` → 阶段 5
- 建图与定位 → 阶段 6
- 导航 → 阶段 7
- 任务状态机 / 自己的控制逻辑 → 阶段 8（现在全靠手动按 teleop）
- 参数化（xacro）→ 阶段 4
- 与实车接口（micro-ROS / MAVLink）→ 阶段 11 对照

**「最小闭环」的意义不是「车能干活」，而是「链条通了、且每一步都能验证」。**

---

## 阶段 4 · 机器人描述工程化（xacro 参数化）

### 本步目标

把「手写 URDF」升级为「参数化 xacro」——**改一个数字，整车尺寸 / 质量 / 惯量跟着变**。

### 为什么需要它（痛点驱动）

阶段 3 的 URDF 里，同一个数字散落多处：

- `0.17`（轮距）出现在：`left_wheel_joint` origin 的 `0.085`、右轮的 `-0.085`、插件 `wheel_separation`
- `0.0325`（轮半径）出现在：`base_joint` 的 z、轮子 cylinder 的 radius、caster 的 z 计算

**改一次轮距要改 3 处**，漏一处就前后矛盾（车走歪 / odom 算错）。

### 三个 xacro 武器

| 武器 | 作用 | 例子 |
|---|---|---|
| `<xacro:property>` | 定义变量 | `wheel_separation = 0.17` |
| `${...}` | 表达式求值 | `${wheel_separation / 2}` |
| `<xacro:macro>` | 复用结构 | 左右轮共用一份定义，传 `reflect=±1` |

**最大收益**：**惯量也用公式算**，改尺寸后不必再手算。

### 文件

- 新增：`urdf/xuegecar_sim.urdf.xacro`（206 行）
- 保留：`urdf/xuegecar_sim.urdf`（阶段 3 版，作为对照材料）
- 改造：`launch/gazebo.launch.py`（改用 `Command(['xacro ', file])` 展开）

### 行为保持验证（重构纪律）

参数化后各量的值，必须与阶段 3 手写版一致。实测（Python 复算同一套公式）：

| 量 | xacro 公式算得 | 阶段 3 硬编码 | 判定 |
|---|---|---|---|
| half_sep | 0.085 | 0.085 | OK |
| wheel_diameter | 0.065 | 0.065 | OK |
| body_z | 0.04 | 0.04 | OK |
| caster_z | -0.0175 | -0.0175 | OK |
| **body_ixx** | **0.0024083333** | **0.002408** | ⚠ 差 0.014% |
| body_iyy | 0.0038666667 | 0.003867 | OK |
| body_izz | 0.0052083333 | 0.005208 | OK |
| wheel_ixx | 2.9739583e-05 | 2.974e-05 | OK |
| wheel_iyy | 5.28125e-05 | 5.281e-05 | OK |
| caster_i | 4.5e-06 | 4.5e-06 | OK |

**关于那个 0.014% 的差异**：不是 bug——是阶段 3 手写时把 `0.0024083333...` 四舍五入成了 `0.002408`。
**xacro 算出的是精确值，比手写版更准。** 参数化保住了行为，还顺手消掉了手写舍入误差。

### 静态检查

- xacro 文件 XML 语法：OK
- launch 的 Python 语法：OK（`python3 -m py_compile`）
- `colcon build`：通过

### 待学生验证（AI 无法代跑）

- `xacro` **未安装** → 需 `sudo apt install ros-humble-xacro`
- 展开验证：`xacro <文件> | head`（结果可观察）
- 启动验证：`ros2 launch xuegecar_sim_bringup gazebo.launch.py`

### 下一步

阶段 5 · 传感器接入（`/scan` `/imu` `/battery_state` `/ultrasonic`）

### 技巧：不装进系统，也能用一个包（本轮实用）

**问题**：阶段 4 需要 `xacro`，但系统里**没装**，而 `sudo apt install` 要密码，AI 代不了。

**解法**：下载 deb → 解包 → `PYTHONPATH` 临时加载。

```bash
# 1. 下载（apt-get download 不需要 root，只下到当前目录）
mkdir -p /tmp/xacro_dl && cd /tmp/xacro_dl
apt-get download ros-humble-xacro

# 2. 解包
dpkg -x ros-humble-xacro_*.deb /tmp/xacro_lib

# 3. 用 PYTHONPATH 临时加载（不写进系统）
export PYTHONPATH=/tmp/xacro_lib/opt/ros/humble/local/lib/python3.10/dist-packages
python3 -c "import xacro; print(xacro.__file__)"
```

**用途**：验证依赖、试用新包、排查版本问题——**不污染环境**。

#### 用这个方法验证阶段 4 的 xacro 文件（全部通过）

| 检查项 | 结果 |
|---|---|
| 展开 | ✅ 成功，输出 169 行 |
| link 数 | 5（base_footprint / base_link / left_wheel / right_wheel / caster） |
| `left_wheel_joint` origin | `0 0.085 0` ✅ |
| `right_wheel_joint` origin | `0 -0.085 0` ✅（`reflect = -1` 与 `half_sep` 的乘法正确） |
| `base_joint` origin | `0 0 0.0325` ✅（来自 `${wheel_radius}`） |
| `wheel_separation` | `0.17` ✅ |
| `wheel_diameter` | `0.065` ✅（来自 `${wheel_radius * 2}`） |
| 惯量 | 全部为公式精确值 ✅ |

**一个被实测否定的担心**：曾怀疑宏参数 `reflect="1"` 是字符串，`${reflect * half_sep}` 会抛 `TypeError`
（Python 里 `"1" * 0.085` 确实会报错，已复现）。
**实测：xacro 会把参数值求值成数字，不会报错。** 担心不成立，但排查过程是对的——**先有假设，再用实测否证**。

### 补充：两个被学生纠正的点 + 一个关键机制（阶段 4）

#### 纠正一：AI 的检查方法有盲区 —— `which xacro` 的假否定

AI 用 `wsl -e bash -c "which xacro"` 判定「xacro 未安装」。
但 **`wsl -e bash -c` 是非交互 shell，不读 `.bashrc`、不 source ROS 环境**，
而 xacro 在 `/opt/ros/humble/bin/` —— 不 source 就找不到。

带 source 重查 + `dpkg -l`：

```
ii  ros-humble-xacro  2.1.1-1jammy  ...   ← 实际早已安装
```

**教训**：**「找不到」不等于「不存在」**——先确认自己的查找条件是否覆盖了目标的真实位置。
（这与「验证方法本身也可能有盲区」是同一条纪律的第二次实例。）

#### 纠正二：AI 漏说了「遥控需要另开终端」

AI 曾写「判据：小车照常出现、照常能遥控」，
但 `ros2 launch xuegecar_sim_bringup gazebo.launch.py` **只做三件事**：

1. 启动 Gazebo；
2. 启动 `robot_state_publisher`；
3. spawn 小车。

**它不启动任何「发指令」的节点**。所以车会站着不动，必须**另开一个终端**跑：

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**教训**：写「判据」时，必须把**隐含的前置步骤**一并写出——读者不该为作者的省略买单。

#### 关键机制：launch 读的是 install 副本（不是 src）

实测 inode 对比：

```
inode=49035  src/.../xuegecar_sim.urdf.xacro
inode=49601  install/.../xuegecar_sim.urdf.xacro     ← 不同 → 是复制出来的副本
```

因为 `get_package_share_directory()` 返回 **install** 路径，
**所以改 `src` 里的 xacro 后，必须 `colcon build` 同步到 `install`**，否则 launch 仍读旧版。

（开发时可用 `colcon build --symlink-install`——建符号链接，src 改动立即生效。）

---

## 阶段 5 · 传感器接入（仿真侧）

### 本步目标

给小车装上 **2D 雷达** 和 **IMU**，让 `/scan` 和 `/imu` 两个话题上线。

### 关键结构：Gazebo 传感器 ≠ ROS 话题

```xml
<gazebo reference="laser_frame">              <!-- ① 挂在哪根 link 上 -->
  <sensor name="laser" type="ray">            <!-- ② Gazebo 的传感器本体 -->
    <ray><scan><horizontal>...</horizontal></scan><range>...</range></ray>
    <update_rate>10</update_rate>
    <plugin filename="libgazebo_ros_ray_sensor.so">   <!-- ③ 桥：把 Gazebo 数据转成 ROS 话题 -->
      <ros><remapping>~/out:=scan</remapping></ros>
      <output_type>sensor_msgs/LaserScan</output_type>
      <frame_name>laser_frame</frame_name>
    </plugin>
  </sensor>
</gazebo>
```

**没有第 ③ 层，Gazebo 里的传感器数据就出不来**——这正是 `gazebo_ros_pkgs` 存在的意义。

### 本步新增的命名对象

| 类型 | 名称 |
|---|---|
| link | `laser_frame`、`imu_link`（都用 `fixed` joint 连到 `base_link`） |
| 话题 | `/scan`（`sensor_msgs/LaserScan`）、`/imu`（`sensor_msgs/Imu`） |
| 插件 | `libgazebo_ros_ray_sensor.so`、`libgazebo_ros_imu_sensor.so` |
| TF | `base_link → laser_frame`、`base_link → imu_link`（RSP 自动发布，无需额外配置） |

### ⚠️ 实测发现的坑：雷达「看到自己」

**第一版**把雷达装在**车体顶面**（z = 0.08）。实测 `/scan`：

```
ranges = [0.0999, 0.1000, ..., 0.0752, 0.1215, ...]    ← 前 87 个值 0.075 ~ 0.124
         后面全是 inf
```

**数值本身就是线索**：`0.075` = 车体**半宽**，`0.100` = 车体**半长** —— 雷达在扫自己的车壳！

**修复**：抬高 2 cm（`laser_standoff = 0.02`）→ 复验：

```
laser_joint z 偏移: 0.0 0.0 0.1
/scan 中「非 inf」读数个数: 0        ← 虚假近距点全部消失
```

**这个过程值得记住**：观察异常 → 提出假设 → **用数值特征验证假设** → 修复 → 复验。

> 这也是**真实工程问题**：真车上的雷达同样需要支架把它抬离车体，否则会测到自己的车壳。

### 空世界里 /scan 全是 inf 是正常的

Gazebo 默认世界里**只有地面、没有障碍物**。2D 雷达水平扫描自然什么都打不到。
想看真实数据，需要往世界里放几个物体。

### 实车 ↔ 仿真 对照

| 话题 | 仿真侧 | 实车侧 |
|---|---|---|
| `/scan` | ✅ `libgazebo_ros_ray_sensor.so` | ✅ Camsense 雷达驱动 |
| `/imu` | ✅ `libgazebo_ros_imu_sensor.so` | ✅ LSM6DS3 驱动 |
| `/battery_state` | ❌ **Gazebo Classic 无官方插件** | ✅ 电池 ADC |
| `/ultrasonic` | ⚠ 可用 ray_sensor 模拟（本阶段未做） | ✅ HC-SR04 |

**`/battery_state` 是「实车有、仿真无」的** —— 又一个差异点，阶段 11 汇总。

### 验证记录（AI 代跑，无头模式）

| 检查 | 结果 |
|---|---|
| 话题 | `/scan` `/imu` 均出现 ✅ |
| `/imu` 数据 | 四元数 w≈1、x/y/z≈0（车水平）✅ |
| `/scan` 数据 | 360 个距离值 ✅（修复后虚假近距点 0 个） |
| 日志错误 | 0 个 ✅ |

### 补充：为什么空世界里 /scan 全是 inf？（学生提问 + 实验证明）

**学生的初始理解**：「世界是平坦的，没有反弹，所以没有有效数据。」

**实测否定**：往世界里加**四面墙 + 一个箱子**（地面依旧是平的）：

```
[非 inf 读数个数] 360        ← 全部 360 个读数都有效
[最小读数] 0.668
[最大读数] 2.752
```

**所以「平坦」不是原因。**

#### 真正的原因：几何（射线方向 vs 物体位置）

2D 雷达是**水平扫描**——360 条射线全部在**同一个水平面**上射出。

```
        雷达（离地约 0.13 m）
   ──────────●──────────      ← 射线在这个高度水平射出
   ════════════════════════    ← 地面（z = 0）
```

**射线与地面平行 → 永远不相交 → 打不到地面。**

- **空世界**：只有地面（在雷达下方）→ 射线什么都碰不到 → 全 `inf`
- **有墙 / 箱子**（高度 1.0 m / 0.5 m，覆盖了 0.13 m 这一层）→ 射线撞上 → 有回波

> **「平坦」无关紧要；「有没有东西立在射线的高度上」才是关键。**

#### 顺带验证了读数的物理正确性

| 读数 | 对应物体 | 几何计算 | 吻合 |
|---|---|---|---|
| 最小 **0.668 m** | 箱子最近角 | 箱子中心 (0.8, 0.5)、半边长 0.2 → 最近角距原点 ≈ 0.67 | ✅ |
| 最大 **2.752 m** | 墙的对角 | 房间 4×4，对角 ≈ 2.83，扣墙厚 0.1 | ✅ |

**数值对得上，说明整条仿真链（URDF 尺寸 → Gazebo 物理 → 雷达射线 → ROS 消息）是准的。**

#### 本次新增的工程产物

- `xuegecar_sim_bringup/worlds/room.world`（4m×4m 房间 + 一个箱子）
- `gazebo.launch.py` 新增 `world:=` 参数（默认 `room.world`）
- `bringup/CMakeLists.txt` 增加安装 `worlds` 目录

**这同时为阶段 6 建图铺好了路**——建图需要一个「有边界的房间」。

### 阶段 6 的技术路线变更（环境约束导致）

**原计划**：GMapping（学生任务书建议）。

**实测环境（apt 源实际可装情况）**：

| 包 | 可装版本 |
|---|---|
| `ros-humble-slam-toolbox` | ✅ 2.6.10 |
| `ros-humble-cartographer` | ✅ 2.0.9004 |
| **`ros-humble-slam-gmapping`** | ❌ **apt 源中不存在** |
| `ros-humble-nav2-bringup` | ✅ 1.1.20 |

**变更**：GMapping → **slam_toolbox**。

**理由**：

1. GMapping 的 ROS2 移植不在 Humble 官方 deb 中，需要源码编译 `openslam_gmapping` + `slam_gmapping`，成本高、易踩编译坑；
2. `slam_toolbox` 是 Humble 官方维护的 2D SLAM；
3. **接口需求与 GMapping 完全一致**：`/scan` + `/odom` + TF → `/map`，学到的知识可完整迁移；
4. 阶段 11 对照真实项目的 GMapping 时，差异落在「实现不同、接口相同」——本身就是好教材。

**安装**：

```bash
sudo apt install ros-humble-slam-toolbox
# 阶段 7 的 Nav2 可一并装：
sudo apt install ros-humble-nav2-bringup ros-humble-navigation2
```

---

## 阶段 6 · 建图与定位（slam_toolbox）

### 为什么选 slam_toolbox（而非 GMapping）

见前节「阶段 6 的技术路线变更」：GMapping 的 ROS2 移植不在 Humble apt 源中。

### 它要什么、给什么

```
/scan ─────┐
           ├──▶ [slam_toolbox] ──▶ /map
/odom ─────┤                   └──▶ TF: map → odom
TF 树 ─────┘
```

**它唯一新增的 TF 是 `map → odom`。**

完整的 TF 链因此变成：

```
map → odom → base_footprint → base_link → laser_frame
 ↑      ↑           ↑               ↑            ↑
SLAM   插件       插件             RSP          RSP
(新增) (已有)     (已有)          (已有)       (已有)
```

### 为什么需要 `map → odom` 这条 TF

- **`odom` 会漂移**：车轮打滑、积分误差、模型误差，走久了就偏了；
- **`map` 不漂移**：它是固定的世界坐标系；
- SLAM 用「看到的环境」估计 odom 的漂移量，**把它补偿掉**。

> **这就是「定位」的本质：用一个不漂移的参考系，去纠正一个会漂移的参考系。**

### 启动（三个终端）

```bash
# 1. 仿真
ros2 launch xuegecar_sim_bringup gazebo.launch.py

# 2. SLAM（自带 launch；use_sim_time 默认就是 true）
ros2 launch slam_toolbox online_async_launch.py

# 3. 遥控（车必须动，地图才会长出来）
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### 验证

```bash
ros2 topic list | grep -E "map|scan"
ros2 topic echo /map --once | head -5
ros2 run tf2_tools view_frames    # 应出现 map → odom → base_footprint → base_link → laser_frame
```

**RViz 里**：Add → Map（Topic 选 `/map`）+ Add → LaserScan（Topic 选 `/scan`），
遥控小车在房间里转一圈，地图应该逐渐「长」出来。

### 常见错误（预判）

| 现象 | 根因 |
|---|---|
| 地图不生成 / 不动 | **车没动**（SLAM 需要运动才能建图） |
| TF 报 `map` 不存在 | slam_toolbox 没启动，或 `use_sim_time` 不一致 |
| 地图扭曲 / 重影 | odom 漂移大，或雷达外参不准 |
| RViz 里看不到地图 | Map display 的 Topic 没设成 `/map`，或 Fixed Frame 不是 `map` |

### 阶段 5 的验证澄清（学生提问）

**学生说**：「没有按键控制，所以反馈的数据都是没有变化的。」

**需分清「没有数据」与「数据不变」**：

| 传感器 | 车静止时 | 车运动时 |
|---|---|---|
| `/scan` | **有数据**（扫到墙/箱子），数值**不变**（视角没变） | 数值**变化** |
| `/imu` | **有数据**（重力方向；角速度≈0、加速度≈−g） | 数值**变化** |

**结论**：「数据不变」≠「没有数据」。车不动时，静态数据是正常的；想看变化，需要让车动起来。

### 阶段 6 验证记录（AI 代跑，无头模式）

**方法**：启动仿真 + slam_toolbox，用 `ros2 topic pub` 驱动小车走 18 秒（0.1 m/s + 0.3 rad/s），再读取 `/map`。

**结果**：

```
地图元信息:
  resolution: 0.05 m/格
  width: 78, height: 78       ← 3.9m × 3.9m，覆盖整个房间

格子分布（6084 格）:
  空闲 (0):   5694 格    ← 房间内部，射线穿过
  占用 (100):  170 格    ← 墙和箱子的可见表面
  未知 (-1):   219 格    ← 未扫到 / 被遮挡
```

**结论：建图成功。** 170 个占用格正好对应四面墙 + 箱子的可见表面。

#### ⚠️ AI 在本阶段连续三次误判——全是「验证方法」的锅

| # | 误判 | 真实原因 |
|---|---|---|
| 1 | 认为「/map 无数据」 | `grep "^width\|^height"` 配合 `head -3`，把字段截掉了 |
| 2 | 认为「格子统计为 0」 | `tr "," "\n"` 后每个值带前导空格，`^0$` 无法匹配 |
| 3 | 认为「slam 没建图」 | `--once` 采样时机 + QoS 读法 |

**三次都不是系统的问题，是检查工具用法的问题。**

> **纪律**：当「检查结果」与「预期」矛盾时，**优先怀疑检查方法**，而不是直接怀疑系统。
> 这条教训在本课已出现多次（`.rviz` 插件类名、`which xacro`、本处三次）。

#### 地图数值的含义

| 值 | 含义 |
|---|---|
| `0` | 空闲（射线穿过，确定无障碍） |
| `100` | 占用（射线命中，确定有障碍） |
| `-1` | 未知（未扫描到） |

**SLAM 的本质**：从「哪里打到了东西」反推「哪里是空的、哪里有墙」。

### 现场排障：小车卡在墙边（阶段 6）

**学生报告**：小车卡墙边、倾斜着一直转圈、导致无法建图。

#### AI 复现结果（无头模式实测）

| 测试 | 结果 |
|---|---|
| 直冲墙 10 秒（0.5 m/s） | 撞后姿态四元数 `x=-6.6e-06, y=6.4e-06, w≈1` → **完全水平，未翻倒** |
| 撞后位置 | `x=1.850` → 车头正好贴住墙面（1.95） |
| 持续顶墙 20 秒（0.3 m/s）后 odom | `x=1.850001` → **无漂移** |

**结论**：物理引擎正常，车只是「贴住墙停住」——真实世界撞墙也会停。

#### 「一直转圈」的可能来源（尚未确认）

1. teleop 按着转向键（`j` / `l`）→ 车贴墙原地转；
2. RViz 中位姿估计跳变，导致车模型乱转；
3. 真的翻车（本次未复现）。

#### 为什么卡住会导致「建图失败」

- 车静止 → `/scan` 不变 → SLAM 无新信息 → 地图**停止更新**（已有地图不会丢）；
- **纯旋转（原地打转）时，2D scan matching 缺少平移约束，容易退化** → 位姿估计漂移 → 地图糊掉。

#### 处理方案

| 场景 | 操作 |
|---|---|
| 车贴墙、没翻 | 反向开出来（`linear.x = -0.1`）或重启 launch |
| 地图已糊 | **重启 slam_toolbox**（清空地图重建） |
| 预防 | 降速（`teleop` 的 `speed:=0.2 turn:=0.5`）；建图时「边走边转」；撞墙先停车 |

#### 认知升级

仿真里 `diff_drive` 能正确检测「轮子被卡住」（odom 不漂移）；
**真实世界不会这么理想**——车轮打滑会让编码器继续计数，odom 照样漂。
这正是阶段 11 要对照的「仿真理想化 vs 真实世界」差异之一。

### 答疑：为什么地图是平面的？（阶段 6）

**学生观察**：RViz 里地图是平面的，没有任何立体东西，墙和方块都显示在平面图上。

**答案：2D SLAM 的地图本来就是二维的，这是物理限制。**

`/map` 的消息类型是 `nav_msgs/OccupancyGrid`：

| 字段 | 含义 |
|---|---|
| `width` / `height` | 栅格尺寸（格子数） |
| `resolution` | 每格多少米 |
| `data` | 每个格子的值：`0`=空闲、`100`=占用、`-1`=未知 |

**没有高度、没有颜色、没有纹理。**

**为什么**：2D 激光雷达只有**一个扫描平面**（水平面，离地约 13 cm）。
它测的是「这个方向多远有东西」，**不测「东西多高」**。

```
侧视图：
     雷达 ────── 射线（水平）
      │
   ───┴──────────────  地面
```

对 2D 雷达来说，一堵墙、一个箱子、一根柱子——只要在同一个高度上，**看起来都一样**（都是一个「有东西」的距离值）。

**要看立体地图**，需要 3D 传感器（多线激光雷达、深度相机）或 3D SLAM（Cartographer 3D、RTAB-Map）。

**而真实项目的 Camsense 也是 2D 雷达** → 建出来同样是平面的。**这是仿真与实车一致的地方。**

### 撞墙脱困：实测有效

| 步骤 | odom.x |
|---|---|
| 前进撞墙（0.5 m/s × 8 s） | 1.850 |
| 按「,」后退（-0.2 m/s × 3 s） | **1.072** |

**后退能脱困**。teleop 键位：`i` 前进、`,` 后退、`j` 左转、`l` 右转、`k` 停止。

### 建图操作要点

**小步走，别长时间按住**：`i` 1 秒 → `k` 停 → `j` 转 → `i` 1 秒 …
长时间按住 = 高速冲撞 = 撞墙。

---

## 阶段 7 · Nav2 导航

### 成功证据（AI 无头实测）

```
发目标前: odom.x = 0.016
发目标后: odom.x = 0.756      ← 车自己走了 0.74 米
TF 错误: 0
目标状态: SUCCEEDED
```

### Nav2 不是一个节点，而是一组服务器

```
目标点 (map 坐标)
   ↓
bt_navigator        ← 行为树：调度整个流程
   ↓
planner_server      ← 全局规划（NavFn / A*）
   ↓
controller_server   ← 局部控制（DWB / TEB）
   ↓
/cmd_vel → 底盘

辅助：
  map_server   → 加载 /map
  amcl         → 定位，发布 map → odom
  global_costmap / local_costmap → 两张代价地图
  behavior_server → 恢复行为（卡住时后退/旋转）
  velocity_smoother → 速度平滑
  lifecycle_manager → 管理所有节点的生命周期
```

### 两张代价地图（最容易混）

| costmap | 范围 | 用途 |
|---|---|---|
| `global_costmap` | 整张地图 | 全局规划（看长远） |
| `local_costmap` | 车周围几米 | 实时避障（看眼前） |

类比：**全局 = 导航软件的路线图；局部 = 你眼睛看的眼前路况。**

### ⚠️ 本轮踩的两个坑（重要教学点）

#### 坑 1：AMCL 需要初始位姿

**现象**：`/amcl_pose` 不发布，Nav2 报 `AMCL cannot publish a pose... Please set the initial pose`。

**原因**：AMCL 不知道车在地图上的初始位置。

**两种解法**：
1. **RViz 里点 `2D Pose Estimate`**（标准做法，真实项目必学）
2. **参数里设**：
   ```yaml
   amcl:
     ros__parameters:
       set_initial_pose: true
       initial_pose: {x: 0.0, y: 0.0, z: 0.0, yaw: 0.0}
   ```

#### 坑 2：AMCL 更新阈值导致「假到达」

**现象**：目标返回 `SUCCEEDED`，但**车一步没动**。

**日志**：
```
[ERROR] [tf_help]: Transform data too old when converting from map to odom
[ERROR] [tf_help]: Data time: 71s, Transform time: 27s   ← TF 落后 44 秒
[INFO]  [controller_server]: Reached the goal!
```

**原因链**：
- AMCL 默认 `update_min_d: 0.25`、`update_min_a: 0.2`
- **车静止 → 不满足更新条件 → AMCL 不更新位姿 → `map→odom` TF 时间戳停在启动时**
- controller 拿到**过期 44 秒的 TF** → 算出的"车到目标距离"错误 → **误判已到达**

**解法**：
```yaml
amcl:
  ros__parameters:
    update_min_d: 0.0
    update_min_a: 0.0
    transform_tolerance: 1.0
```

> **这个坑的价值**：它说明 **TF 不只是"坐标"，还带"时间"**。
> 时间戳过期的 TF，会让上层算法基于旧世界做决策。

### 关键参数（按我们的车改）

| 参数 | 值 | 为什么 |
|---|---|---|
| `robot_radius` | 0.125 | 车的外接圆半径（0.20×0.15 的对角线/2） |
| `inflation_radius` | 0.30 | 障碍物膨胀距离（默认 0.55 太大，4×4 房间过不去） |
| `max_vel_x` | 0.26 | 最大线速度 |
| `update_min_d` / `update_min_a` | 0.0 | AMCL 每帧更新 |
| `set_initial_pose` | true | 启动时给初始位姿 |

### 启动（三终端）

```bash
# [终端 A] 仿真
ros2 launch xuegecar_sim_bringup gazebo.launch.py

# [终端 B] Nav2
ros2 launch nav2_bringup bringup_launch.py \
  map:=/home/y/my_map.yaml \
  params_file:=/home/y/xuegecar_sim_ws/src/xuegecar_sim_bringup/config/nav2_params.yaml \
  use_sim_time:=true

# [终端 C] RViz
rviz2 -d ~/xuegecar_sim_ws/src/xuegecar_sim_description/rviz/xuegecar_sim.rviz
```

**RViz 操作**：Fixed Frame → `map`；Add → Map(`/map`)；Add → Path(`/plan`)；
用 **2D Goal Pose** 点目标（若 params 已设初始位姿，则不必点 2D Pose Estimate）。

### 坑：RViz 报 "No map received" —— QoS Durability 不匹配（阶段 7）

**实测证据**：

```
/map 发布者 (map_server):  Reliability: RELIABLE,  Durability: TRANSIENT_LOCAL
/map 订阅者 (rviz):        Reliability: RELIABLE,  Durability: VOLATILE
/map 订阅者 (amcl):        Reliability: RELIABLE,  Durability: TRANSIENT_LOCAL
```

**根因**：`map_server` 以 **TRANSIENT_LOCAL（latched）** 发布地图；
RViz 的 Map display 默认用 **VOLATILE** 订阅 → **收不到订阅之前已发布的那条消息**。
而地图很少更新 → RViz 一直收不到 → `No map received`。

**修复（RViz 界面内）**：
Displays → Map → 展开 `Topic` → **`Durability Policy`：`Volatile` → `Transient Local`** → 地图立刻出现。

#### QoS 兼容规则表（通用，值得记住）

| 发布者 | 订阅者 | 兼容？ | 说明 |
|---|---|---|---|
| RELIABLE | RELIABLE | ✅ | 标准 |
| RELIABLE | BEST_EFFORT | ✅ | 订阅方降级 |
| **BEST_EFFORT** | **RELIABLE** | ❌ | **连不上** |
| TRANSIENT_LOCAL | TRANSIENT_LOCAL | ✅ | 能收历史消息 |
| TRANSIENT_LOCAL | VOLATILE | ⚠️ | 能连，但**收不到历史**（地图/机器人描述类话题的常见坑） |
| **VOLATILE** | **TRANSIENT_LOCAL** | ❌ | 连不上 |

**判断方法**：
```bash
ros2 topic info /话题 -v
```
对比发布端 / 订阅端的 `Reliability` 与 `Durability`。**QoS 不匹配时 DDS 静默失败，不报错。**

#### 本课出现过两次同类问题

1. `/robot_description`（RSP → RViz RobotModel）：同样需要 `Transient Local`
2. `/map`（map_server → RViz Map）：本次

> **规律：凡是「内容不常变、新人来了要能立刻看到」的话题（地图、机器人描述、静态参数），
> 多半是 latched（TRANSIENT_LOCAL）发布的；订阅端必须也用 TRANSIENT_LOCAL。**

### 坑：RViz 工具栏找不到 `2D Goal Pose`（阶段 7）

**根因**：AI 给的 `.rviz` 配置里，`Visualization Manager → Tools` 只列了
`MoveCamera / Select / FocusCamera / Measure`，**没有 `SetGoal`**。
RViz 的工具栏只显示 **配置里声明过的工具** —— 没声明就没有按钮。

**类名**（已用 RViz 插件注册表核实）：
- `rviz_default_plugins/SetGoal` → 工具栏的 `2D Goal Pose`
- `rviz_default_plugins/SetInitialPose` → 工具栏的 `2D Pose Estimate`

**修复后的 `.rviz` 关键段**：

```yaml
  Tools:
    - Class: rviz_default_plugins/MoveCamera
    - Class: rviz_default_plugins/Select
    - Class: rviz_default_plugins/FocusCamera
    - Class: rviz_default_plugins/Measure
    - Class: rviz_default_plugins/SetInitialPose
      Topic: {Value: /initialpose}
    - Class: rviz_default_plugins/SetGoal
      Topic: {Value: /goal_pose}
```

**同时补齐的显示项**（阶段 7 所需）：
Grid / RobotModel（Transient Local）/ Map（Transient Local）/ Path（`/plan`）/ LaserScan（Best Effort）

**教训**：`.rviz` 不是"显示配置文件"，它同时**声明了可用工具**。
换一个 `.rviz` 就等于换了一套工具栏。

### 坑：Nav2 有绿色路径但车不动（阶段 7）

**现象**：用 `2D Goal Pose` 点目标后，RViz 出现绿色路径（`/plan` 有数据），但车一步不动。

#### AI 复现结果（无头模式，远目标）

```
初始 odom.x = 0.016
发目标 (1.5, 1.5)
8 秒后 /cmd_vel: linear.x = 0.26      ← controller 正常发速度
8 秒后位置: x=1.306, y=1.503         ← 车移动 1.3 米
```

**结论：Nav2 本身正常。** 问题在「目标点」。

#### 最可能原因：目标离车太近

`xy_goal_tolerance: 0.25` ——
**目标距离 < 25 cm 时，controller 直接判定「已到达」，不会发任何速度。**

**症状**：
- 绿色路径极短（甚至看不见）
- `/cmd_vel` 无数据
- 任务状态 `SUCCEEDED`

**正确做法**：点一个**远目标**（房间另一头），路径应贯穿地图。

#### 排障顺序（若远目标仍不动）

| # | 检查 | 命令 | 判读 |
|---|---|---|---|
| 1 | controller 是否发速度 | `ros2 topic hz /cmd_vel` | 有数据 → 物理层问题 |
| 2 | AMCL 位姿 | `ros2 topic echo /amcl_pose --once --field pose.pose.position` | 与真实位置差距大 → 定位漂了 |
| 3 | Nav2 日志 | 看 `Reached the goal!` | 出现 → 误判到达（目标近/TF 旧） |
| 4 | 旧任务残留 | 重启 Nav2 | 旧任务未结束会挡住新目标 |

#### 判据：什么算「导航成功」

- 绿色路径**从车延伸到目标**（长度合理）
- `/cmd_vel` 出现非零 `linear.x` / `angular.z`
- `odom` 位置**持续变化**
- 最终 `SUCCEEDED`，且车停在目标附近

---

## 阶段 8 · 任务状态机与安全逻辑

### 为什么状态机不是「写个 switch」

大多数人第一次做状态机，会写一个 `if state == "NAVIGATING": ...` 的节点，让它跟遥控器**同时**往 `/cmd_vel` 发速度。这个做法在真车上会直接导致「急停不生效」：

```
teleop  ──0.2 m/s──► /cmd_vel
状态机  ──0.0 m/s──► /cmd_vel     ← 两条命令在同一条话题上，谁后到算谁的
```

`/cmd_vel` 是**普通话题，不是命令队列**：多个发布者同时写，订阅端（底盘）只看到"最近收到的这一条"。teleop 每 0.5 秒发一条 0.2，状态机就算连发十次零速，只要 teleop 还在按着，车就不会停。

所以真正要做的第一件事不是写状态机，而是**建立唯一的速度出口**：

```
teleop ─┐
Nav2   ─┼─► /cmd_vel ─► [任务状态机] ─► /cmd_vel_motor ─► 底盘插件
急停    ─┘              唯一发布者
```

> **判据**：底盘只订阅一个话题，且这个话题只有一个发布者。
> 只要这条不成立，"急停"就只是一种建议，不是一种保证。

### 阶段 8 拆成 6 步（每步独立可验证）

| 步 | 加什么 | 验收判据 |
|---|---|---|
| 8.1 | 底盘改听 `/cmd_vel_motor`（装闸门） | `/cmd_vel` 无订阅者；往 `/cmd_vel_motor` 发速度车会动 |
| 8.2 | 状态机进程骨架 + 直通转发 | teleop 恢复能动；`/mission_state` 打出 `IDLE` |
| 8.3 | 急停（ESTOP） | 行驶中触发急停，车 0.5 秒内停住，且**不会自己恢复** |
| 8.4 | 看门狗（数据超时） | 杀掉 `/odom` 源，2 秒内自动进 `ERROR` 并停车 |
| 8.5 | 状态迁移表（准入条件） | 未建图时进不了 `NAVIGATING` |
| 8.6 | 接 Nav2 Action + 错误恢复 | 目标失败 → `ERROR` → `/reset` → `IDLE` |

---

### 8.1 装闸门：让底盘只认一个话题

#### 改什么（一行）

`xuegecar_sim_description/urdf/xuegecar_sim.urdf.xacro`，差速插件的 `<ros>` 块内（现 **L290**）：

```xml
<plugin name="diff_drive" filename="libgazebo_ros_diff_drive.so">
  <ros>
    <namespace>/</namespace>
    <remapping>cmd_vel:=cmd_vel_motor</remapping>
  </ros>
```

`libgazebo_ros_diff_drive.so` 内部用相对名 `cmd_vel` 订阅速度（已用 `strings` 核实该字符串存在），`<remapping>` 把它的订阅目标改到 `/cmd_vel_motor`。**改的是底盘的耳朵，不是说话的人**——因此不需要动 teleop、不需要动 Nav2，它们照旧往 `/cmd_vel` 发，只是暂时没人听。

同一套机制本项目已经用过一次：雷达插件里 `<remapping>~/out:=scan</remapping>`。

#### 为什么不用「状态机也发 /cmd_vel + 抢话题」

见上文。抢话题做不到「切断」，只能做到「比谁发得勤」。真车、仿真、Nav2 三者叠加时，这种实现 100% 会出「急停后车还在走」的事故。

#### 实测记录（AI 代跑）

隔离实例：`ROS_DOMAIN_ID=42`、`GAZEBO_MASTER_URI=http://127.0.0.1:11399`、`gui:=false`——不干扰学生同时开着的 Gazebo/Nav2/RViz 会话（实测时确有 3 个活动终端在跑）。

| 检查 | 结果 |
|---|---|
| `/cmd_vel` 端点 | `Unknown topic '/cmd_vel'`（**0 发布者 0 订阅者**） |
| `/cmd_vel_motor` 端点 | 订阅者数 1，`Node name: diff_drive` |
| 往 `/cmd_vel` 发 `linear.x=0.2` | 阻塞在 `Waiting for at least 1 matching subscription(s)...`，车不动 |
| 往 `/cmd_vel_motor` 发 `linear.x=0.2` | `odom.x: 0.011 → 0.821`（约 4 秒，0.2 m/s ✓） |
| 往 `/cmd_vel_motor` 发 `linear.x=0.0` | 停稳后 `odom.x: 1.0387 → 1.0382`（抖动 < 1mm，确实停了） |

#### 学生验证（4 个终端，注意顺序）

```bash
# [终端 A] 先 Ctrl+C 掉当前 launch —— 你正在跑的那个 gzserver 还是旧配置
ros2 launch xuegecar_sim_bringup gazebo.launch.py

# [任意终端] 闸门装好了吗
ros2 topic info /cmd_vel_motor -v      # 应看到 diff_drive 的 SUBSCRIPTION
ros2 topic info /cmd_vel -v            # 应显示 0 个端点

# [终端 C] 遥控 —— 预期「按 i 车不动」，这不是坏了
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# [任意终端] 手动给油门，车应该动
ros2 topic pub -r 10 /cmd_vel_motor geometry_msgs/msg/Twist "{linear: {x: 0.1}}"
```

#### 三个必须记住的现象

1. **按 `i` 不动是正确行为**。它证明闸门真的在物理通路上，不是在代码注释里。
2. **`Ctrl+C` 停发 ≠ 停车**。底盘会保持最后收到的速度一直走——这是真车电机的共性，也是 8.3「急停必须主动发零速并持续发」的原因。
3. **一条零速命令到车真正停住之间有几百毫秒**（本次实测滑行了约 0.2 米才停稳）。所以急停不能只发一次，要在一个循环里持续发，直到 `odom` 证实速度为 0。

> 代价：从 8.1 到 8.2 之间，**遥控和 Nav2 都会暂时失效**（它们还在发 `/cmd_vel`，没人听）。
> 这是刻意的——先把闸门装好，再把钥匙交出去。

---

### 8.2 状态机骨架 + 直通转发

#### 新增的包与文件

```
src/xuegecar_sim_mission/            ← ament_python 包
├── package.xml                      rclpy / geometry_msgs / std_msgs
├── setup.py                         entry point: mission_control
├── setup.cfg
├── resource/xuegecar_sim_mission
└── xuegecar_sim_mission/
    ├── __init__.py
    └── mission_control.py           状态 + 唯一速度出口（约 100 行）
```

#### 它现在连接的四个话题

| 方向 | 话题 | 类型 | 说明 |
|---|---|---|---|
| 入 | `/cmd_vel` | `geometry_msgs/Twist` | 所有速度来源（teleop / Nav2） |
| 出 | `/cmd_vel_motor` | `geometry_msgs/Twist` | 唯一出口，底盘只认这个 |
| 出 | `/mission_state` | `std_msgs/String` | 当前状态，1 Hz 周期发布（latched 效果靠周期重发） |
| 入 | `/mission_command` | `std_msgs/String` | 切换命令（8.6 升级为 action/srv） |

#### 三个设计决定（以及为什么）

1. **速度放行用白名单**（`VELOCITY_ALLOWED = {'TELEOP'}`）。以后加 `NAVIGATING` 就是往集合里加一项；**漏加的状态默认不放行**。反过来写成黑名单 `if state == 'IDLE': return`，以后新增 `ERROR` 忘了加，结果就是错误状态下照样能开车。这叫 fail-closed。
2. **切换用话题而不是服务**。`std_srvs/SetBool` 表达不了 7 个状态，自定义 srv 现在还不值得；话题两行命令就能测。等 8.6 接 Nav2 时再升成 action。
3. **不设 `use_sim_time`**。节点只用自己的时钟做超时判断（8.4 会按「收到消息的时刻」打时间戳，而不是比较消息头里的仿真时间）——真机上时钟不同步是常态，按接收时刻计时更稳。

#### 实测记录（AI 代跑，隔离实例 ROS_DOMAIN_ID=42 / :11399）

| # | 检查 | 结果 |
|---|---|---|
| 1 | `/cmd_vel_motor` 端点 | 发布者 1 = `mission_control`；订阅者 1 = `diff_drive` ✓ |
| 2 | `/mission_state` | `data: IDLE` |
| 3 | `IDLE` 下发 `/cmd_vel 0.2` | `odom.x: 0.00618 → 0.00754`（<1.5 mm，纯求解器抖动）→ **挡住了** |
| 4 | 切 `TELEOP` 后发 `/cmd_vel 0.2` | `odom.x: 0.00754 → 0.8162` → **放行了** |
| 5 | 节点日志计数 | `state=TELEOP 转发=1 拦截=1` |
| 6 | 未知状态命令 `{data: FLYING}` | 日志 `拒绝迁移：未知状态 'FLYING'`，状态不变 |

#### ⚠️ 8.2 的已知缺口（这是 8.3 存在的理由）

**切出 TELEOP 之后车不会自己停。** 实测（干净复测）：

```
倒退 0.15 m/s，切 IDLE 前          odom.x = 1.5425
切 IDLE 后                        odom.x = 1.0779
再等 3 秒                         odom.x = 0.4702      ← 还在以 0.15 m/s 倒退
```

原因不是状态机写错了，而是**底盘的行为**：差速插件收到一条速度就一直执行，没人发零速它就不会停。状态机只是"不再转发"，而"不再转发" ≠ "发零速"。

> 这一条必须记住：**任何"停止命令"的本质都是「主动发一条零速并持续确认它生效」，而不是「不再发速度」。**
> 8.3 的急停就补在这里——切出 TELEOP 时主动发零速，且在 ESTOP 状态里以 20 Hz 持续发。

#### 一个验证方法上的坑（差点写出假结论）

第一次测这个缺口时，数据是 `1.8500 → 1.8499`，看起来"切 IDLE 后车立刻停了"，差点据此写下"缺口不存在"。实际是：在切 IDLE 之前，车已经以 0.2 m/s 跑了十几秒、**撞在墙上**（房间 4×4，墙在 ±2.0，卡住时 odom.x≈1.85），撞墙和切状态两个变量混在一起，观测被污染。

教训：**测"某个动作是否让车停"时，必须先确认车在观测窗口内本来是有能力动的**（远离墙壁、有足够行程、速度方向朝开阔处）。上一节（阶段 6）的"AI 连续三次误判"也是同一类错误——错在验证方法，不在代码。

#### 学生验证（5 步）

```bash
# [终端 A] 仿真（若已在跑就跳过）
ros2 launch xuegecar_sim_bringup gazebo.launch.py

# [终端 D] 启动状态机 —— 新开一个终端
ros2 run xuegecar_sim_mission mission_control

# [终端 X] 看状态（应该是 IDLE）
ros2 topic echo /mission_state

# [终端 C] 遥控 —— 此时按 i 仍然不动（IDLE 不放行）
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# [终端 X] 切到 TELEOP，然后回终端 C 按 i —— 车应该动
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: TELEOP}"

# [终端 X] 观察计数（转发数应随你按 i 增长）
#   日志在终端 D 里，每 2 秒一行 state=... 转发=... 拦截=...
```

#### 用户级验收（AI 用伪终端代按真键，用的是真的 `teleop_twist_keyboard`）

按键不是靠 `ros2 topic pub` 模拟的——把 teleop 放进 `script -qec` 的伪终端里，等 3 秒（确认它已进入 raw 模式）再 `printf 'i'`，这样按下的是学生真正会按的那个键。

| 验收 | 动作 | 数据 | 结论 |
|---|---|---|---|
| A | `IDLE` 下按 `i` | `odom.x: 0.00360 → 0.00801`（4.4 mm） | 不动 ✓ 拦截计数 +1 |
| B | 切 `TELEOP` 后按 `i` | `odom.x: 0.00954 → 1.85000`（走 1.84 m） | 能动 ✓ 转发计数 +4 |
| C | `TELEOP` 下按 `k` | `0.73502 → 0.73568 → 0.73636`（累计 0.69 mm） | 停住 ✓ |

C 用的是"按 i 走 1.5 秒（约 0.73 m）再按 k"的序列——**从原点出发、离墙足够远**，这是刻意设计的，见下。

#### 同一个坑踩了两次：撞墙污染观测

验 C 的第一次尝试，数据是 `1.8500 → 1.84999`，怎么看都是"按 k 后一动不动"。但那次车在按 k 之前就已经撞墙停在 1.85 了——**撞墙和按 k 两个变量叠在一起，观测无效**。

改成"从原点出发、先走 0.73 m 再按 k"之后，才拿到 `0.73502 → 0.73636` 这种能说明问题的数据（0.69 mm 是物理引擎的静摩擦抖动，不是运动）。

> **判据**：验收任何"让车停下来"的动作，先问一句「在这个观测窗口里，车本来有能力动吗？」
> —— 起点离墙够远、行程够长、速度方向朝开阔处。否则你测到的是墙，不是你的代码。

#### 顺带确认的一个 teleop 细节

真按 `i` 之后 teleop 会**持续**以 0.5 m/s 发布（不是按一次发一条），所以 A/B 之间必须用 `k` 明确停车，不能指望"松开键就停"。这也解释了为什么 `IDLE` 下按 `i` 之后车不会因为"按键结束"而动——它压根没收到过放行的速度。

---

### 8.3 急停：从「不转发」到「真的停」

#### 这一版加了三个机制

| 机制 | 实现 | 为什么需要 |
|---|---|---|
| 立刻清零 | `_set_state()` 里，目标状态不在放行名单时立刻 `publish(Twist())` | 底盘上一条命令可能是 0.3 m/s，必须**主动覆盖**，不能等 |
| 持续压零速 | 20 Hz 定时器 `enforce_safe()`，ESTOP 里每 50 ms 发一帧零速 | 底盘没有「命令过期」概念；单帧可能丢；50 ms 比任何速度源都密 |
| 粘性急停 | `STICKY = {'ESTOP'}`，只有 `RESET` 能离开 | 急停不能被下一个命令冲掉，必须由人显式复位 |

#### 为什么不「销毁订阅」

一个直觉做法是急停时 `destroy_subscription(cmd_sub)`，物理切断输入。问题：重新启用要重建 DDS 连接，恢复延迟几百毫秒，而且「订阅还在但状态不放行」本来就已经拦住了。**拦截 + 零速压制**既能挡住输入，又能主动纠正底盘的残留速度，比销毁订阅更彻底。

#### 实测（探针节点：同一条时间轴里发命令 + 采 `/odom`，避开 CLI 发现延迟）

| 步骤 | 观测 |
|---|---|
| 切 TELEOP，发 `0.3 m/s` | `x=0.4059, vx=0.300` |
| **发 ESTOP** | `x=0.4059`（发命令瞬间） |
| 首次观测到 `abs(vx)<0.01` | **+310 ms**，`x=0.4541`，急停后**多走 48.2 mm** |
| ESTOP 里再发 `0.5 m/s` | `x: 0.4537 → 0.4535`（0.2 mm，纹丝不动），state 仍 ESTOP |
| ESTOP 下发 `TELEOP` | state **仍是 ESTOP**（粘性，日志 `拒绝迁移：ESTOP 是粘性状态，必须先发 RESET`） |
| 发 `RESET` | state → `IDLE` ✓ |
| 20 Hz 计数 | 约 2 秒内 39 帧（19.5 Hz ✓） |
| 从 IDLE 直接发 ESTOP | 成功进入，日志 `!!! 急停：IDLE → ESTOP` ✓ |

#### 那 310 ms 是从哪来的（这道题可以算出来）

`xuegecar_sim.urdf.xacro` **L301**：

```xml
<max_wheel_acceleration>1.0</max_wheel_acceleration>
```

差速插件对轮速的变化率做了限幅。若它限制的是**轮子线速度**（m/s²），那么从 `0.3 m/s` 减到 `0` 需要：

```
t = v / a = 0.3 / 1.0 = 0.3 s
```

**实测 310 ms。** 两个独立来源（参数推导 + 实测）吻合，说明这个限幅确实是 1 m/s²。

> 教学结论：**急停的「最后一米」不在你的 Python 里，在底盘的加速度限幅里。**
> 状态机能在 1 帧内发出零速（<50 ms），但轮子要从 0.3 m/s 停下来，物理上要 0.3 秒、多走 4.8 厘米。
> 真车上这段距离由电机惯性和减速机决定，想把急停做快，得动硬件（抱闸）或改 `max_wheel_acceleration`——但那会让所有加速/减速都变粗暴。

#### 另一个必须知道的边界

这次进的 `ESTOP` 是由人（或脚本）触发的。**系统自己发现危险时怎么进 ESTOP**，那是 8.4 看门狗的事：
数据超时 → 自动进 `ERROR`（不是 ESTOP——因为「数据没了」和「人按了急停」在语义上不同，
复位条件也不同）。8.4 会把 `SAFETY_HOLD` 扩成 `{'ESTOP', 'ERROR'}`，两个状态都压零速。

#### 学生验证（6 步）

```bash
# [终端 A] 仿真    [终端 D] ros2 run xuegecar_sim_mission mission_control
# [终端 C] teleop

# 1. 切 TELEOP，按 i 让车走起来
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: TELEOP}"

# 2. 车走着的时候急停（另开 [终端 X]）
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: ESTOP}"
# 判据：车在 0.3 秒内停住，多走不超过 5 厘米；终端 D 出现 ERROR 级日志「!!! 急停」

# 3. 急停状态下继续按 i —— 车不动
# 4. 直接发 TELEOP —— 被拒绝，state 仍是 ESTOP
ros2 topic echo /mission_state --once

# 5. 复位
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: RESET}"
# 判据：state → IDLE，此时按 i 仍不动（IDLE 不放行）

# 6. 回 TELEOP 确认车能动，收工
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: TELEOP}"
```

---

## 补课：轮子是怎么转起来的（一条 Twist 的完整旅程）

> 这一节回答「我不理解轮子相关的内容」。它不属于某个阶段，是贯穿阶段的底层机制。

### 1. URDF 里，一个轮子由两样东西组成

```
link（轮子本身）               joint（轮子怎么装在车上）
├─ visual/collision: 圆柱      ├─ type="continuous"   能无限转（不是 fixed 不能动、不是 revolute 有角度限位）
│  radius=0.0325  length=0.02  ├─ origin xyz="0 ±0.085 0"  装在车的左右两侧
├─ inertial: 质量 0.1kg        ├─ axis xyz="0 1 0"    绕 y 轴转
│  转动惯量按圆柱算             └─ limit velocity="20" 最大 20 rad/s
```

对应 `xuegecar_sim.urdf.xacro` **L110-135**（`wheel` 宏）。

**为什么 axis 是 y 轴**：ROS 的坐标约定是 **x 前、y 左、z 上**（REP-103）。轮子要"向前滚"，转轴就必须横向——也就是 y 轴。右手定则验一下：绕 +y 转，轮子最低点的速度指向 −x，所以车身被推向 +x（前进）。**轴的符号决定"正转是前进还是后退"，写反了车就会倒着走。**

### 2. 三个轮子的高度是自洽算出来的

```
wheel_radius   = 0.0325   轮心到地面
base_link      = z 0      定在轮心高度（所以轮心就在车身坐标原点）
caster_z       = caster_radius - wheel_radius = 0.015 - 0.0325 = -0.0175
                → 球心在轮心下方 1.75cm，球底 = -0.0175 - 0.015 = -0.0325 = 轮底 ✓
```

**两轮 + 一个万向球 = 三点支撑。** 少一个球，车会前后翻（两个轮子共轴，重心正压在轴上，一加速就低头）。

### 3. Twist → 轮速：差速逆运动学（Gazebo 插件干的活）

差速车的两个轮子只有两种运动组合：**同速 = 直行，反速 = 原地转**。

```
v_left  = v − ω · W/2
v_right = v + ω · W/2          W = wheel_separation = 0.17 m
```

| 你发的 Twist | 左轮线速度 | 右轮线速度 | 轮子转速（rad/s = v/r） |
|---|---|---|---|
| `linear.x=0.3` | 0.3 | 0.3 | 各 9.23（≈88 rpm，1 秒滚 1.5 圈） |
| `angular.z=1.0` | −0.085 | +0.085 | 左 −2.62、右 +2.62（原地左转 57°/秒） |
| `x=0.2, z=0.5` | 0.1575 | 0.2425 | 差速转弯 |

轮子转一圈车走 `2πr = 0.204 m`——这就是"轮半径"这个数字的全部意义：**v 和 ω 是抽象的，半径把它们翻译成轮子转多快。**

### 4. 轮速 → odom：正运动学（同样由插件算）

```
d_left  = θ_left  · r        θ = 轮子转过的角度（joint 状态）
d_right = θ_right · r
车位移   Δs = (d_left + d_right) / 2
车朝向   Δθ = (d_right − d_left) / W
```

累计这些 Δ 就是 `/odom`。**所以 odom 是"数轮子转了多少圈"推算出来的，不是测量的**——轮子打滑、地面不平、半径标定不准，误差就会一直累积。这就是为什么建图/导航还需要雷达 + AMCL 来纠偏：`map → odom` 修正，`odom → base_footprint` 由轮子积分。

### 5. 整条链路

```
你的键盘 i
  └─ teleop_twist_keyboard → /cmd_vel (Twist, 0.5 m/s)
       └─ mission_control  ── 状态是 TELEOP?
            └─ /cmd_vel_motor
                 └─ gazebo_ros_diff_drive（50 Hz）
                      ├─ 逆运动学：v_left/v_right = 0.5 −/+ …
                      ├─ 加速度限幅：max_wheel_acceleration = 1.0 m/s²
                      ├─ 转成 joint 速度 → Gazebo 物理引擎 → 轮子真的转
                      └─ 读 joint 角度 → 正运动学 → /odom + odom→base_footprint TF
```

**急停那 310 ms 就卡在"加速度限幅"这一行**：0.3 m/s ÷ 1.0 m/s² = 0.3 s，代码发零速只要一帧，轮子减速要 0.3 秒。

### 6. 三个容易混的数字

| 数字 | 值 | 管什么 |
|---|---|---|
| `wheel_radius` | 0.0325 m | 线速度 ↔ 轮转速的换算 |
| `wheel_separation` | 0.17 m | 直行 ↔ 转弯的分配（W 越小转得越急） |
| `update_rate` | 50 Hz | 插件多久算一次、发一次 odom |

---

### 8.4 看门狗：系统自己坏了怎么办

#### 核心认知：ROS 里「没有消息」不会触发任何回调

订阅回调只在**有消息**时执行。所以「多久没收到」这件事，**订阅端是感知不到的**——必须另设一个定时器，自己拿表去比：

```python
# 有消息时只做一件事：记下时刻
def on_odom(self, msg):
    self.last_rx['odom'] = time.monotonic()

# 定时器（10 Hz）负责判断「多久没收到」
def check_links(self):
    now = time.monotonic()
    for name in self.MONITORED:
        age = now - self.last_rx.get(name, self.start_time)
        if age > self.timeouts[name]:
            self._set_state('ERROR')
```

这就是看门狗与普通订阅的本质差别：**普通订阅是「事件驱动」，看门狗是「时间驱动」**。

#### 三个设计决定

| 决定 | 实现 | 为什么 |
|---|---|---|
| 超时进 `ERROR`，不是 `ESTOP` | `STATES += 'ERROR'`，`SAFETY_HOLD` 扩成 `{'ESTOP','ERROR'}` | 语义不同：ESTOP 是人叫停，ERROR 是故障。日志、复位条件、外部 UI 都应该区分 |
| 故障未消除时拒绝 `RESET` | `faults_cleared()` 检查每个源最近是否有数据 | 否则「复位 → 立刻超时 → ERROR」来回抖，人永远不知道什么时候真的好了 |
| 启动宽限期 5 秒 | `now - start_time < grace` 时直接返回 | 刚启动还没收到数据是正常的，否则一启动就 ERROR |

**数据恢复后不自动回 IDLE**，这一点是刻意的：故障可能是间歇性的（接触不良、DDS 偶发丢包），自动恢复会让车「自己开始动」。必须人工确认后 `RESET`。

#### 参数（可调，不用改代码）

| 参数 | 默认 | 依据 |
|---|---|---|
| `odom_timeout` | 0.5 s | odom 50 Hz（20 ms/帧）→ 0.5 s = 丢 25 帧 |
| `scan_timeout` | 1.0 s | 雷达 10 Hz（100 ms/帧）→ 1.0 s = 丢 10 帧 |
| `grace_period` | 5.0 s | 覆盖 Gazebo 启动 + spawn 的时间 |

调法：`--ros-args -p odom_timeout:=1.0`。

#### 实测证据（两轮）

**第一轮：SIGSTOP 冻结 gzserver**

| 步骤 | 观测 |
|---|---|
| 宽限期后 | `state=IDLE`，日志 `[odom=0.01s scan=0.07s]` → **不误报** ✓ |
| `kill -STOP` 冻结 | `!!! 看门狗：/odom 已 0.57s 无数据（阈值 0.50s）→ ERROR，已强制零速` ✓ |
| 零速帧率 | 日志 2 秒内 47 → 87 帧 = **20 Hz** ✓ |
| 数据未恢复时 RESET | `拒绝复位：故障未消除 —— /odom（0.5s 内无数据）、/scan（1.0s 内无数据）` ✓ |
| `kill -CONT` 解冻 | 日志 `state=ERROR 数据已恢复，可以 RESET` ✓ |
| 恢复后 RESET | `ERROR → IDLE` ✓ |
| **解冻后发 0.3 m/s** | **x: 0.0091 → 0.0106（只有 1.5 mm）——车没动** ⚠️ |

**第二轮：起一个新 gazebo 实例（新 master 端口 11400），模拟「底盘重启」**

| 步骤 | 观测 |
|---|---|
| 基线 TELEOP 发 0.3 | `x: 0.0048 → 1.6979`（1.69 m）✓ |
| 杀掉 gzserver | `!!! 看门狗：/odom 已 0.56s 无数据 → ERROR，已强制零速` ✓ |
| 未恢复时 RESET | 保持 `ERROR` ✓ |
| 新 gazebo 起来（spawn=1） | 状态**仍 ERROR**（不自动恢复）✓ 日志 `数据已恢复，可以 RESET` |
| 恢复后 RESET | `ERROR → IDLE` ✓ |
| 再 TELEOP 发 0.3 | `x: 0.0057 → 1.5008`（**1.50 m，车真的能动**）✓ |

**结论：产品逻辑（超时→ERROR→拒复位→恢复→复位→能动）全部成立。**

#### ⚠️ 又一次「观测手段本身污染结论」（第三次了）

第一轮用 SIGSTOP 冻结仿真，逻辑全对，但最后一步「车能不能动」测出来是 1.5 mm——差点据此写下「恢复后车动不了」这个假结论。

差异说明问题不在产品逻辑：**第二轮换成「杀掉 gzserver，再起一个全新实例」，同样的代码路径，车走了 1.5 米。**

真实原因（未深究到底层）：SIGSTOP/SIGCONT 让 Gazebo 的仿真时钟与物理线程停顿了几秒，恢复瞬间 `dt` 异常大，差速插件的速度积分被带偏。**这是测试脚手架的副作用，不是被测代码的缺陷。**

教训：**测「恢复后能否工作」时，要用真实的恢复方式（重启进程），不要用暂停/继续这种非真实操作。** 前两次分别是「撞墙污染急停观测」「按键未进 raw 模式」，这是第三次——手法不同，根因同一个：**验证装置和被测对象共享了状态**。

#### 学生验证（5 步）

```bash
# [终端 A] 仿真    [终端 D] 重启一次状态机（旧进程加载的是 8.3 代码）
ros2 run xuegecar_sim_mission mission_control
# [终端 X] 切 TELEOP
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: TELEOP}"

# ① 正常时不该报错：等 10 秒，看终端 D 的 [odom=…s scan=…s] 都接近 0
# ② 制造故障：另开终端执行 killall gzserver
#    ⚠️ 只关 Gazebo 窗口不管用：gui_required 默认 false，关窗口只结束 gzclient，
#       gzserver 还在跑、/odom 继续发，看门狗不会触发。
#       依据：/opt/ros/humble/share/gazebo_ros/launch/gzclient.launch.py:92
#             /opt/ros/humble/share/gazebo_ros/launch/gzserver.launch.py:199
#    判据：2 秒内终端 D 出现「!!! 看门狗：/odom 已 0.5xs 无数据 → ERROR」
# ③ 此时 RESET —— 应被拒绝，并列出 /odom、/scan 都无数据
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: RESET}"
# ④ 重启仿真（终端 A 重新 ros2 launch …）
#    判据：状态仍是 ERROR（不会自己恢复），日志变成「数据已恢复，可以 RESET」
# ⑤ 再 RESET —— 这次成功回 IDLE；切 TELEOP 后按 i 车能动
```

#### 判据表

| 现象 | 含义 |
|---|---|
| 正常时日志 `[odom=0.0xs scan=0.0xs]` | 数据健康，看门狗在正常巡检 |
| 2 秒内变 ERROR 并打印超时源 | 看门狗工作 |
| RESET 被拒且列出无数据的源 | 故障未消除保护生效 |
| 数据恢复后仍 ERROR | 不自动恢复，等人确认 |
| 数据恢复后 RESET 成功 → 能动 | 全链路闭环 |

---

## 附录：WSL 重启后的完整恢复与验收流程

> 适用场景：`wsl --shutdown` 或关机重开之后，从零把系统跑起来并验收 8.1-8.4。
> 前提：`~/xuegecar_sim_ws/install` 已存在（编译产物在磁盘上，重启不丢），**不需要重新 build**。

### 0. 启动 WSL

开始菜单搜 Ubuntu / Windows Terminal 选 Ubuntu / `wsl` 回车。

**判据**：出现 `y@主机名:~$`。

### 1. 环境自检

```bash
echo $ROS_DISTRO                          # 应为 humble
ls ~/xuegecar_sim_ws/install | grep xuegecar
```

**判据**：`humble` + 三个包（description / bringup / mission）。
`~/.bashrc` 的 L120/L122 已自动 source ROS 与工作区，正常终端不需要手动 source；若 `$ROS_DISTRO` 为空，执行 `source ~/.bashrc`。

### 2. 开四个终端

| 终端 | 职责 |
|---|---|
| A-仿真 | `ros2 launch xuegecar_sim_bringup gazebo.launch.py` |
| D-状态机 | `ros2 run xuegecar_sim_mission mission_control` |
| C-遥控 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` |
| X-命令 | 发 `/mission_command`、查话题 |

### 3. 启动顺序与判据

| 步 | 终端 | 命令 | 判据 |
|---|---|---|---|
| 1 | A | `ros2 launch xuegecar_sim_bringup gazebo.launch.py` | Gazebo 窗口 + `Successfully spawned entity` |
| 2 | D | `ros2 run xuegecar_sim_mission mission_control` | `看门狗已启用…` + `state=IDLE … [odom=0.01s scan=0.07s]` |
| 3 | C | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` | 打印键位表 |

> 终端 D 看不到 `看门狗已启用` = 跑的是旧代码 → `cd ~/xuegecar_sim_ws && colcon build --packages-select xuegecar_sim_mission`

### 4. 验收 8.1（闸门）

```bash
ros2 topic info /cmd_vel_motor -v | grep -E "count|Node name"
```

**判据**：发布者 1 = `mission_control`；订阅者 1 = `diff_drive`。

### 5. 验收 8.2（拦截/放行）

| 步 | 操作 | 判据 |
|---|---|---|
| 1 | 确认 `ros2 topic echo /mission_state --once` = `IDLE` | — |
| 2 | 终端 C 按 `i` | 车**不动**，`拦截=` +1 |
| 3 | `{data: TELEOP}` | 日志 `IDLE → TELEOP` |
| 4 | 终端 C 按 `i` | 车动，`转发=` 上涨 |
| 5 | 终端 C 按 `k` | 车停住 |

### 6. 验收 8.3（急停）

| 步 | 操作 | 判据 |
|---|---|---|
| 1 | 按 `i` 走 1 秒，车还在走时发 `{data: ESTOP}` | ~0.5 s 内停住（0.5 m/s ÷ 1.0 m/s²），多走约 12 cm；日志 `!!! 急停` |
| 2 | 按 `i` | 不动，`拦截=` 增长 |
| 3 | 发 `{data: TELEOP}` | 被拒（`ESTOP 是粘性状态`），状态仍 ESTOP |
| 4 | 发 `{data: RESET}` | `ESTOP → IDLE` |
| 5 | 按 `i` | 不动（IDLE 不放行） |
| 6 | 发 `{data: TELEOP}` | 能动 |

### 7. 验收 8.4（看门狗）

| 步 | 操作 | 判据 |
|---|---|---|
| 1 | 等 10 秒 | 不是 ERROR，`[odom=0.0xs scan=0.0xs]` |
| 2 | **`killall gzserver`**（只关窗口不够，见下） | 2 秒内 `!!! 看门狗：/odom 已 0.5xs 无数据 → ERROR` |
| 3 | 发 `{data: RESET}` | 被拒，列出 `/odom`、`/scan` |
| 4 | 终端 A 重新 launch，等 20 秒 | 状态**仍 ERROR**，日志 `数据已恢复，可以 RESET` |
| 5 | 发 `{data: RESET}` | `ERROR → IDLE` |
| 6 | 切 `TELEOP`，按 `i` | 能动（实测恢复后走 1.50 m） |

### 8. 收尾

```bash
killall gzserver gzclient
```

**直接关终端窗口会留孤儿 gzserver，下次启动报 `Address already in use`。**

### 故障速查

| 现象 | 处理 |
|---|---|
| `ros2: command not found` | `source ~/.bashrc` |
| `Package 'xuegecar_sim_mission' not found` | 同上 |
| 按 `i` 不动且 `转发` 不涨 | 状态不是 TELEOP |
| 按 `i` 不动但 `转发` 在涨 | 查 `/cmd_vel_motor` 订阅者是否 `diff_drive` |
| `Address already in use` | `killall gzserver` 等 3 秒再起 |
| 终端 D `[odom=未见]` | 仿真没起或刚起，等 15 秒 |
| RESET 没反应 | 只在 ESTOP/ERROR 下有效，日志会提示 |
| 撞墙后动不了 | 先查状态是否仍 TELEOP；按 `,` 后退可脱困（实测 0.69 m） |

#### 8.4 修正：看门狗只在「需要运动」的状态里监控

**问题**（学生实测发现）：只启动 `mission_control`、没起仿真时，5 秒宽限一过就进 ERROR：

```
state=IDLE 转发=0 拦截=0 [odom=未见 scan=未见]
IDLE → ERROR
!!! 看门狗：/odom 已 5.01s 无数据（阈值 0.50s）→ ERROR，已强制零速
```

**根因不是看门狗写错，是监控范围写宽了。** `IDLE` 是待机态——底盘可能没上电、传感器没插，这些都不该算故障。真正需要数据健康的是「车要动」的时候。

**修法**（3 行）：

```python
WATCHDOG_ACTIVE_IN = {'TELEOP'}      # 只在工作态监控

def check_links(self):
    if self.state not in self.WATCHDOG_ACTIVE_IN:
        return                        # IDLE 待机不查；STOP/ERROR 也不查
```

**实测**（隔离实例）：

| 场景 | 结果 |
|---|---|
| 只起状态机、不起仿真，等 10 秒（远超 5 秒宽限） | 保持 `IDLE`，日志 `[odom=未见 scan=未见]` 但**不报错** ✓ |
| 随后起仿真 | 仍 `IDLE`，日志变 `[odom=0.00s scan=0.08s]` ✓ |
| 切 `TELEOP` 后杀 gzserver | `0.57 s` 内 `!!! 看门狗：/odom 已 0.57s 无数据 → ERROR` ✓ |
| 未恢复时 RESET | 被拒 ✓ |
| 新实例恢复后 RESET | `ERROR → IDLE` ✓ |

**顺带解决的体验问题**：启动顺序不再敏感。以前「先起状态机、后起仿真」必然 ERROR（Gazebo 要 15 秒才 spawn 完，宽限只有 5 秒）；现在两种顺序都可以。

**留下的问题（8.5 解决）**：如果底盘从未上线，切 `TELEOP` 后仍会立刻 ERROR。更好的做法是**在迁移前做准入检查**——数据不健康就拒绝进入 `TELEOP`，而不是先进去再报错。这是 8.5 迁移表的一部分。
