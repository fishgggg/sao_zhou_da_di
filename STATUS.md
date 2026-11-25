# STATUS.md —— 当前状态与下一步

> **这是唯一的进度真相。** 任何「已完成」的声称，必须能指到一条实测记录（日志、`ros2 topic echo`、截图）。
> 阶段 0–11 的历史细节看 `阶段8接续说明.md`（已归档，不再更新）。
> 最后更新：2026-11-25

---

## 一、当前阶段

**扫地机器人分支 · M0 整合 —— 已完成**

主线计划见 `扫地机器人分支计划.md`。

| 里程碑 | 状态 | 一句话验收 |
|---|---|---|
| M0 整合 | ✅ 完成 | 新会话读 `PROJECT.md` 即可接手 |
| M1 三室一厅 + 建图 | ⬜ 未开始 | 地图完整、尺寸误差 < 5% |
| M2 跨房间导航 + 避障 | ⬜ 未开始 | 10 次跨房间 ≥ 8 成功，动态障碍能绕 |
| M3 覆盖清扫 | ⬜ 未开始 | 单房间覆盖率 ≥ 85%，重复 < 20%，零碰撞 |
| M4 回充 + 状态发布 | ⬜ 未开始 | 低电量自动回充，状态/事件字段完整 |

---

## 二、遗产基线（阶段 0–11，已实测）

| 能力 | 状态 | 证据 |
|---|---|---|
| Gazebo + 差速底盘 + `/odom` + TF | ✅ | 阶段 3 |
| 参数化 URDF（xacro，改一个数字整车跟着变） | ✅ | 阶段 4 |
| `/scan` 10Hz + `/imu` 100Hz | ✅ | 阶段 5 |
| SLAM 建图（slam_toolbox） | ✅ | 阶段 6，`~/my_map` 83×83 |
| Nav2 点到点导航 | ✅ | 阶段 7 |
| 任务状态机 + 安全层（唯一速度出口） | ✅ | 阶段 8，`mission_control.py` 489 行 |
| 一条命令起全套 + namespace 隔离 | ✅ | 阶段 9 |
| 回归脚本 11 项断言 | ✅ | 阶段 10，`scripts/regression.sh` |
| 实车 13 包对照（接口几乎逐字一致） | ✅ | 阶段 11 |

**边界（不要说过头）**：实车跑的是开源原版，安全层（状态机/急停/看门狗）是仿真改进，**未上实车**。

---

## 三、M0 交付记录（2026-11-25）

| 动作 | 结果 |
|---|---|
| 新增 `PROJECT.md` | 三处路径锚点 + 环境坑 + 构建运行命令 + 文档索引 |
| 新增 `STATUS.md` | 本文件 |
| 新增 `扫地机器人分支计划.md` | M0–M4 施工蓝图 + 接口契约 |
| WSL `~/xuegecar_sim_ws` 建 git | 首次提交 `a48f3be`，20 个文件（3 个包） |
| 记忆库提交 | 文档入库 |

**实测事实（本轮核实，不是回忆）**：

- `~/xuegecar_sim_ws` 此前**没有** git（`fatal: not a git repository`）——阶段 8 的代码改动之前无版本追溯
- `nav2_waypoint_follower`、`nav2_collision_monitor`、`slam_toolbox` 均已安装（source 后 `ros2 pkg list` 328 个包）
- 雷达：360 线 / −180°~180° / 0.05–12.0 m / 10 Hz（`xuegecar_sim.urdf.xacro` L40–45）
- 车体 0.20×0.15×0.08，轮距 0.17，轮半径 0.0325
- Nav2：`xy_goal_tolerance` 0.25、`inflation_radius` 0.30、`cost_scaling_factor` 3.0
- `room.world` 4×4 m，5 个 model；world 目录只有这一个文件

---

## 四、遗留问题（按优先级）

### P0 · 必须在 M2 之前解决

**1. 取消导航后再导航，车不动**

- 现象：Nav2 `controller_server: Failed to make progress` + `[follow_path] Aborting handle`；`/cmd_vel` 20 Hz 但内容全 0
- 已排除：mission 转发正常（1184 帧），不是状态机的问题
- 判断：Nav2 abort 后 recovery 卡住
- 当前规避：重启 Nav2
- **影响面**：单房间时偶发；多房间序列任务里「取消/重规划」是常态，不修会让 M3 每段任务断在第二段

**2. 重启 Nav2 后容器卡住**

- 现象：`ros2 action info /navigate_to_pose` → `Action servers: 0`；`component_container_isolated` 起来了但无 lifecycle 日志
- 当前表现：mission 拒绝目标是正确行为（不是 bug）

### P1 · 功能缺口（M3/M4 会碰到）

**3. `MAPPING` / `LOCALIZING` 只是状态名**

没有和 `slam_toolbox` / AMCL 自动联动。计划里不阻塞 M1–M4，但「状态语义 = 现在允许什么」这条设计承诺目前对这两个状态是空的。

**4. 多房间任务没有房间概念**

代码里没有「房间」，只有坐标。M3.2 的 `rooms.yaml` 是补这个缺口的第一步。

### P2 · 记录但暂不处理

**5. 文档历史矛盾**：`ROS2小车项目结构详解.md` 中雷达型号在 4.1 / 4.6 两处不一致（YDLIDAR vs camsense_lidar）。实车代码目录里是 `camsense_lidar` 包。仿真侧与型号无关，不影响 M1–M4；写简历或面试引用时按代码为准。

---

## 五、下一步（M1）

**第一件事**：写 `worlds/three_rooms.world`（12 m × 10 m，客厅 + 三卧 + 走廊，家具用 `<box>`）。

顺序：

1. 设计平面图（先画在纸上定坐标，再写 SDF，别边写边想）
2. 复制 `room.world` 的 `<world>` 骨架改（保留物理引擎、光照、地面）
3. 建图并保存 `three_rooms.pgm/yaml`
4. 核对尺寸精度、回环闭合
5. `room.world` 保持不动（回归用）

验收判据见 `扫地机器人分支计划.md` M1。

---

## 六、验证记录

| 日期 | 命令 | 结果 |
|---|---|---|
| 2026-11-25 | `wsl -e bash -lc 'cd ~/xuegecar_sim_ws && git init …'` | 成功，`a48f3be`，`git ls-files` 20 个文件 |
| 2026-11-25 | `ros2 pkg list \| grep -E "^nav2_waypoint_follower$\|^nav2_collision_monitor$\|^slam_toolbox$"` | 三个包全部存在，总数 328 |
| 2026-11-25 | 未执行：任何 ROS 运行时（仿真/导航/回归） | 本轮只做文档与版本控制，未跑仿真 |

> 本表只记真实跑过的命令。没跑的不写「应该没问题」。
