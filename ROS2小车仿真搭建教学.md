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
