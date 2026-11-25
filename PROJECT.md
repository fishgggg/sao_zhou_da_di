# PROJECT.md —— 项目总部锚点

> 新会话只读这一份，就能知道：代码在哪、怎么跑、做到哪一步。细节按需再跳转。
> 最后更新：2026-11-25（M0 整合）

---

## 一、三处路径与读写边界

| 角色 | 路径 | 权限 | 说明 |
|---|---|---|---|
| **记忆库（总部）** | `D:\笔记位置存放\Agent项目记忆库\ROS2小车的项目` | 可读写 | 文档、计划、状态。git 仓库 |
| **仿真代码（主战场）** | WSL `Ubuntu-22.04` → `~/xuegecar_sim_ws` | 可读写 | ROS 2 工作区，3 个包。git 仓库（M0 建立） |
| **实车代码（对照源）** | `C:\Users\Y\Desktop\ros_car\xuegeros_ws\xuegeros_ws\src` | **只读** | 14 个包，开源原版。不入库、不改动 |
| **实车固件** | `C:\Users\Y\Desktop\ros_car\leap_demo` | **只读** | ESP32 底盘/摄像头固件，仅作参考 |

Windows 与 WSL 是两套文件系统。**不要在 `/mnt/d` 上跑 `colcon build`**：慢，且会丢 Linux 可执行权限位。

---

## 二、环境

- WSL2 / Ubuntu 22.04 / ROS 2 Humble / Gazebo Classic 11
- 已装关键包：`slam_toolbox`、`navigation2`（含 `nav2_waypoint_follower`、`nav2_collision_monitor`）、`nav2_bringup`、`teleop_twist_keyboard`、`xacro`、`gazebo_ros_pkgs`
- 地图文件：`~/my_map.pgm` + `~/my_map.yaml`（83×83 @ 0.05 m，阶段 6 产物）

### 一个环境陷阱

从 Windows 侧调 WSL 时，`wsl -e bash -c` **不读 `.bashrc`**，`ros2` / `xacro` 会报「命令未找到」。必须显式 source：

```bash
wsl -e bash -lc 'source /opt/ros/humble/setup.bash && source ~/xuegecar_sim_ws/install/setup.bash && <命令>'
```

这个坑曾让「包明明装了却 list 不到」——诊断前先确认 source 了没有。

---

## 三、构建与运行

### 构建

```bash
wsl -e bash -lc 'source /opt/ros/humble/setup.bash && cd ~/xuegecar_sim_ws && colcon build && source install/setup.bash'
```

改了 `xuegecar_sim_description` 后**必须重新 build**，launch 读的是 `install/` 里的副本，不是 `src/`。

### 常用命令

| 用途 | 命令 |
|---|---|
| 起仿真（Gazebo + RSP + spawn） | `ros2 launch xuegecar_sim_bringup gazebo.launch.py` |
| 一条命令起全套 | `ros2 launch xuegecar_sim_bringup bringup.launch.py` |
| 任务状态机 | `ros2 run xuegecar_sim_mission mission_control` |
| 建图（SLAM） | `ros2 launch slam_toolbox online_async_launch.py` |
| 导航（Nav2） | `ros2 launch nav2_bringup bringup_launch.py map:=/home/y/my_map.yaml params_file:=~/xuegecar_sim_ws/src/xuegecar_sim_bringup/config/nav2_params.yaml use_sim_time:=true` |
| 遥控 | `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_teleop` |
| 切状态 | `ros2 topic pub --once /mission_command std_msgs/msg/String "{data: TELEOP}"` |
| 回归 | `bash ~/xuegecar_sim_ws/src/xuegecar_sim_bringup/scripts/regression.sh` |
| 杀仿真 | `killall gzserver gzclient`（别直接关窗口） |

**注意**：阶段 8 后底盘听 `/cmd_vel_motor`，`/cmd_vel` 不再是底盘入口。直接发 `/cmd_vel` 必须先把状态切到 `TELEOP`。

---

## 四、当前主线

**扫地机器人分支改造（M0–M4）** —— 详见 `扫地机器人分支计划.md`。

一句话：把现有仿真小车改造成能在三室一厅里自主建图、避障、覆盖清扫、自动回充的扫地机器人；对外接口按契约预留，将来接 LLM agent 时机器人侧零改动。

当前进度见 `STATUS.md`（唯一的进度真相）。

---

## 五、版本控制

| 位置 | 状态 |
|---|---|
| 记忆库 | git（本仓库），提交历史即文档演进 |
| 仿真代码 `~/xuegecar_sim_ws` | git（M0 建立），提交即代码基线 |
| 实车代码 / 固件 | 上游开源，不入库，只读 |

**纪律**：改仿真代码前先确认工作区干净（`git status`），改完单独提交。没有基线的改动等于没有改动——出问题无法回滚，也无法判断是谁引入的。

---

## 六、文档索引

| 文档 | 用途 | 什么时候读 |
|---|---|---|
| `PROJECT.md` | 本文，路径与环境锚点 | 每次开场 |
| `STATUS.md` | 当前状态、遗留问题、下一步 | 每次开场 |
| `扫地机器人分支计划.md` | M0–M4 施工蓝图 + 接口契约 | 动手前、设计讨论 |
| `阶段8接续说明.md` | 阶段 0–11 的历史交付与踩坑清单（已归档，不再更新） | 查历史细节 |
| `ROS2小车仿真搭建教学.md` | 11 阶段完整讲义（160KB，含实测数据） | 查原理、查坑的成因 |
| `ROS2小车项目结构详解.md` | 实车 14 包的结构与接口 | 查实车对照 |
| `ROS2小车项目资料.md` | 实车开源项目资料（静态阅读整理） | 同上 |
| `ROS2基础补课.md` | 8 课基础概念（坐标系/SLAM/costmap/QoS 等） | 概念不清时 |
| `面试问题和答案.md` | 仿真 20 题 + 实车 A-F 组 | 面试准备 |
| `ROS小车.md` | 简历素材库（量化成果、三档文案、证据分级） | 写简历时 |
| `项目经验（服务简历）.md` | 实车项目的简历描述 | 同上 |

---

## 七、几条不要重复踩的坑

1. `colcon build` 成功但 `ros2 pkg list` 看不到 → 没 `source install/setup.bash`
2. RViz RobotModel / Map 空白 → `/robot_description` 和 `/map` 是 `TRANSIENT_LOCAL`，RViz 的 QoS 要对
3. 雷达扫到自己（0.075/0.100 m 假点）→ 雷达要抬离车体顶面（standoff 0.02）
4. Nav2 目标 `SUCCEEDED` 但车不动 → AMCL `update_min_d` 导致 TF 时间戳变旧（已改 0.0）
5. 急停「反应慢」约 0.3 秒 → 不是代码慢，`max_wheel_acceleration=1.0`，物理上就要这么久
6. 阶段 8 后按 `i` 车不动 → 底盘改听 `/cmd_vel_motor`，且状态必须是 `TELEOP`
7. 急停后发 `TELEOP` 无效 → `ESTOP` 是粘性的，先发 `RESET`
8. 验证「车停没停」时数据全 0 → 先确认车在观测窗口内本来能动（远离墙、行程够长）

完整 14 条见 `阶段8接续说明.md` 第六节。
