# sao_zhou_da_di · 仿真扫地机器人

ROS 2 Humble + Gazebo Classic 的差速小车，正在从「能导航」改造成「能打扫三室一厅的扫地机器人」。

> 起点是一个开源的 ROS 2 差速小车（实车，13 个包）。我先在仿真里把它的能力逐层重建，跑通建图、定位、导航和任务状态机；现在开始把它往扫地机器人改，并预留 LLM agent 的接入接口。

---

## 进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| 基础重建 0–11 | 环境 / 架构 / 包 / 最小闭环 / xacro / 传感器 / SLAM / Nav2 / 任务状态机 / 命名空间 / 回归测试 | ✅ 已在对应会话实测并记录 |
| M0 整合 | 路径锚点、状态文档、代码版本基线 | ✅ |
| M1 三室一厅 | 12×10 m 场景与建图 | ⬜ 进行中 |
| M2 跨房间导航 + 避障 | 含两个 Nav2 遗留问题的修复 | ⬜ |
| M3 覆盖清扫 | 弓字路径 + 沿墙 + 覆盖率度量 | ⬜ |
| M4 回充 + 状态接口 | 低电量回充、CleanCommand / RobotState / RobotEvent | ⬜ |

详细验收判据见 [`docs/扫地机器人分支计划.md`](docs/扫地机器人分支计划.md)。

---

## 已有能力

- **仿真闭环**：Gazebo 差速底盘 + `/odom` + TF + RViz，遥控 → `/cmd_vel_motor` → 轮子
- **参数化机器人**：xacro 定义车体（0.20×0.15×0.08 m，轮距 0.17 m，轮半径 0.0325 m），改一个数字整车跟着变
- **传感器**：2D 雷达 360 线 / 0.05–12 m / 10 Hz，IMU 100 Hz
- **建图**：slam_toolbox，产出 83×83 @ 0.05 m 栅格地图
- **导航**：Nav2 点到点，costmap 三层（static + obstacle + voxel）
- **任务状态机**：7 状态（`IDLE` / `TELEOP` / `MAPPING` / `LOCALIZING` / `NAVIGATING` / `ESTOP` / `ERROR`）+ 急停 + 看门狗 + 速度源分权
- **回归**：11 项断言的 `regression.sh`

### 一个设计上值得说的点

**唯一速度出口**：底盘插件的订阅被 remap 到 `/cmd_vel_motor`（xacro 里一行改的），任何速度源（遥控、Nav2、将来的清扫规划器）都必须经过 `mission_control` 的闸门。

```text
teleop / Nav2 ──► /cmd_vel(_teleop) ──► mission_control ──► /cmd_vel_motor ──► diff_drive
                                              ▲   │
                              /mission_command│   │/mission_state
```

放行逻辑是白名单 fail-closed：`VELOCITY_ALLOWED = set(SOURCE_BY_STATE)`——新加的状态默认**不放行**，必须显式加入。这一条让「加功能」和「加危险」在代码层面天然分离。

---

## 目录结构

```
.
├── docs/                       设计与状态文档（先读 PROJECT.md 和 STATUS.md）
├── sim_ws/                     ROS 2 包镜像（从 WSL 工作区同步而来）
│   ├── src/xuegecar_sim_description/   参数化 URDF + RViz 配置
│   ├── src/xuegecar_sim_bringup/       launch / world / Nav2 参数 / 回归脚本
│   └── src/xuegecar_sim_mission/       任务状态机（mission_control.py）
└── scripts/sync-code.sh        从 WSL 工作区同步代码到 sim_ws/
```

**`sim_ws/` 是镜像，不是构建位置。** 实际开发在 WSL 的 `~/xuegecar_sim_ws`（ext4）。不要在 `/mnt/d` 上跑 `colcon build`：Node 模块量级的小文件 IO 会让编译慢一个数量级，而且 Linux 可执行权限位在挂载盘上会丢。

同步规则（单向，永远以 WSL 为准）：

```bash
bash scripts/sync-code.sh
```

---

## 快速开始

需要 WSL2 + Ubuntu 22.04 + ROS 2 Humble + Gazebo Classic 11。

```bash
# 1. 放到 WSL 的 Linux 文件系统里（不要在 /mnt 下构建）
git clone git@github.com:fishgggg/sao_zhou_da_di.git ~/sao_zhou_da_di
mkdir -p ~/xuegecar_sim_ws && cp -r ~/sao_zhou_da_di/sim_ws/* ~/xuegecar_sim_ws/

# 2. 构建
cd ~/xuegecar_sim_ws
colcon build
source install/setup.bash

# 3. 起仿真
ros2 launch xuegecar_sim_bringup gazebo.launch.py

# 4. 起任务状态机（另一个终端）
ros2 run xuegecar_sim_mission mission_control

# 5. 切到遥控态，再接遥控（否则按 i 车不动，这是设计）
ros2 topic pub --once /mission_command std_msgs/msg/String "{data: TELEOP}"
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_teleop
```

地图与依赖包（`slam_toolbox`、`navigation2`、`nav2_bringup`、`teleop_twist_keyboard`、`xacro`）需自行安装。

---

## 能力边界（别读过头）

- **实车跑的是开源原版**。本仓库里的安全层（状态机、急停、看门狗）是仿真侧的改进，**没有上过实车**。
- 仿真里的「清扫」目前只是规划与覆盖，没有真实清洗物理（吸力、尘盒都是状态模拟）。
- M1–M4 尚未完成，进度以 `docs/STATUS.md` 为准。

---

## 文档

| 文档 | 内容 |
|---|---|
| [`docs/PROJECT.md`](docs/PROJECT.md) | 路径锚点、环境、构建运行命令 |
| [`docs/STATUS.md`](docs/STATUS.md) | 当前进度、遗留问题、下一步（唯一进度真相） |
| [`docs/扫地机器人分支计划.md`](docs/扫地机器人分支计划.md) | M0–M4 施工蓝图 + 接口契约 |
| [`docs/阶段8接续说明.md`](docs/阶段8接续说明.md) | 阶段 0–11 交付物与 14 条踩坑清单 |
| [`docs/ROS2小车仿真搭建教学.md`](docs/ROS2小车仿真搭建教学.md) | 11 阶段完整讲义（含实测数据） |
| [`docs/ROS2基础补课.md`](docs/ROS2基础补课.md) | 坐标系 / SLAM / costmap / QoS 等概念补课 |
| [`docs/ROS2小车项目结构详解.md`](docs/ROS2小车项目结构详解.md) | 实车 13 包的结构与接口对照 |

---

## License

本仓库中的仿真代码与文档为自己编写；实车开源项目的许可信息见其原始仓库。
