# ROS2 基础补课 · 从坐标系到导航栈

> 用途：面试补基础。按“能串起来”而不是“按字母顺序”组织。
> 每课结构：一句话定义 → 谁发布 → 为什么需要 → 面试怎么答 → 自测题。

---

## 课程地图

| 课 | 主题 | 一句话 |
|---|---|---|
| **1** | 三坐标系 map/odom/base_link | 一个是全局参考，一个是连续参考，一个是车体本身 |
| 2 | odom 的本质 | 推算不是测量，所以会漂，而且不修正自己 |
| 3 | SLAM vs AMCL | 一个建图并定位，一个只在地图里定位；都发布 `map→odom` |
| 4 | costmap（两种） | 全局规划看整张图，局部避障看眼前 |
| 5 | Nav2 的五个角色 | planner / controller / behavior / bt_navigator / lifecycle |
| 6 | TF 的时间戳 | TF 不只是坐标，还带时间；过期的 TF 会让上层基于旧世界做决策 |
| 7 | QoS | 不匹配时静默失败，是“收不到数据”的第一嫌疑 |
| 8 | Topic / Service / Action | 广播 / 请求-应答 / 长任务 + 反馈 + 可取消 |

---

# 第 1 课 · 三个坐标系

## 1.1 一句话定义

| frame | 是什么 | 谁发布它的变换 | 会跳吗 | 用来干什么 |
|---|---|---|---|---|
| `map` | **全局**参考系，原点在地图里某个固定点 | SLAM 或 AMCL | **会**（重定位时突变） | 全局规划、目标点、给人看 |
| `odom` | **连续**参考系，原点在机器人开机时所在位置 | 底盘驱动 / Gazebo 差速插件 | 不会跳，但会**漂** | 局部控制、平滑运动 |
| `base_link` / `base_footprint` | **车体本身** | `robot_state_publisher`（从 URDF） | 不跳不漂（刚体） | 所有传感器的挂载基准 |

## 1.2 为什么必须三个，不能合并成两个

这是面试的核心追问。

**假设只有 `map` 和 `base_link`**：那车的位姿必须由 `map→base_link` 直接给出。而 `map→base_link` 来自定位（AMCL）。定位会在重定位时**跳变**——粒子收敛到新位置，车在 map 里的坐标突然从 (1.0, 0.5) 跳到 (2.3, 0.1)。

**跳变的后果**：控制器看到“位置突变 1.3 米”，会算出巨大的速度指令，车会猛打方向或猛加速。

**所以引入 `odom` 作为缓冲层**：

```
map → odom      ← 允许跳变（AMCL 修正）
odom → base_link ← 连续平滑（轮子积分）
```

控制器只用 `odom→base_link` 做局部控制，**永远不会看到跳变**；全局规划用 `map`，跳一下就跳一下，重新规划即可。

**一句话**：`odom` 是“给控制器的连续参考”，`map` 是“给规划器的全局参考”，中间用 `map→odom` 这个可跳变的修正量连接。

## 1.3 三者的关系式（面试杀手题）

车在地图里的位姿，不是 AMCL 直接发出来的，而是**两次变换相乘**：

```
T(map → base_link) = T(map → odom) × T(odom → base_link)
                        ↑                ↑
                   AMCL 发布        底盘驱动发布
```

**AMCL 从不发布车在 map 里的坐标**——它只发布 `map→odom` 的修正量。
你在 RViz 里看到的车在地图上的位置，是 tf2 把这两段乘出来的。

> 面试如果问“AMCL 发布什么”，答“`map→odom` 变换 + `/amcl_pose`（车位姿，方便观察）”，比答“发布车的位置”准确一个档次。

## 1.4 base_link 和 base_footprint 为什么是两个

| | base_footprint | base_link |
|---|---|---|
| 位置 | 车**在地面的投影**，z=0 | 车体几何中心 |
| 高度差 | — | 通常 +0.04m（本项目车体高 0.08 的一半） |
| 谁用 | 导航栈（costmap 的 `robot_base_frame`）、里程计 | 传感器挂载、URDF 的 link 树 |

**为什么导航要用 base_footprint**：地面车只关心平面位置，z 恒为 0 能让 2D costmap 的投影干净。如果用 base_link（z=0.04），每个激光点都要减 4cm 才落到地面。

两者之间是一个 **fixed joint**，`robot_state_publisher` 从 URDF 自动发布，不需要你写代码。

## 1.5 这三个 frame 谁发、发到哪

| 变换 | 发布者 | 话题 | 频率 |
|---|---|---|---|
| `map → odom` | AMCL 或 SLAM | `/tf` | 跟激光/更新阈值（本项目设成每帧都发） |
| `odom → base_footprint` | 差速插件 / 底盘驱动 | `/tf` | 50Hz（插件 update_rate） |
| `base_footprint → base_link` | robot_state_publisher | `/tf_static` | 一次（fixed joint） |
| `base_link → laser_frame` | robot_state_publisher | `/tf_static` | 一次（fixed joint） |

**注意 `/tf` 和 `/tf_static` 是两条话题**：
- `/tf_static` 存**不变**的变换（fixed joint），QoS 是 TRANSIENT_LOCAL（晚来的订阅者也能收到）
- `/tf` 存**会变**的变换，VOLATILE

## 1.6 面试怎么答（背这一段）

> “ROS2 导航栈用三个坐标系。`map` 是全局参考，原点在地图里，SLAM 或 AMCL 发布 `map→odom`；`odom` 是连续参考，原点在开机位置，底盘驱动发布 `odom→base_footprint`；`base_link` 是车体本身，由 `robot_state_publisher` 从 URDF 发。
>
> 分三个的原因是**跳变隔离**：AMCL 重定位时 `map→odom` 会突变，如果控制器直接用 `map→base_link`，它就看到位置瞬移，会输出巨大的速度指令。有了 `odom` 这层，控制器只用连续的 `odom→base_link`，永远不会被跳变影响。
>
> 车在 map 里的位姿是两次变换相乘：`map→base_link = (map→odom) × (odom→base_link)`。AMCL 本身不发布车的位置，它只发布 `map→odom` 这个修正量。”

## 1.7 自测题

1. 车在 RViz 里突然“跳”了 1 米，但 `/odom` 数据是连续的——哪个变换变了？
2. 如果我把底盘驱动的 `publish_odom_tf` 关掉，只留 AMCL，会怎样？
3. 为什么 `/tf_static` 用 TRANSIENT_LOCAL，而 `/tf` 用 VOLATILE？

<details>
<summary>答案</summary>

1. `map→odom`（AMCL 修正）。odom→base 连续说明轮子积分没问题。
2. `odom→base_footprint` 没了，tf2 断链，所有依赖 `map→base_link` 的节点（costmap、RViz）全部查不到变换 → 导航直接瘫。
3. `/tf_static` 内容不变，晚启动的节点也要能拿到（否则 RViz 后开就看不到车模型）；`/tf` 每帧都在变，没有必要保留历史，保留反而占内存。

</details>

---

# 第 2 课 · odom 的本质（预告）

**一句话**：`odom` 是**数轮子转了多少圈推算出来的**，不是测量的，所以误差只会累积、不会自愈。

待展开：
- 差速正运动学公式
- 为什么打滑、地面不平、轮径标定不准都会引入误差
- 为什么不能靠 odom 单独导航（十分钟能漂几十厘米）
- EKF 怎么用 IMU 修正它

---

# 第 3 课 · SLAM vs AMCL（预告）

**一句话**：SLAM 建图 + 同时定位，AMCL 只在已知地图里定位；两者都发布 `map→odom`，所以**同一时刻只能有一个在发**。

待展开：
- gmapping / cartographer / slam_toolbox 的区别
- AMCL 的粒子滤波直觉
- 为什么建图时不能同时开 AMCL（两个发布者抢 `map→odom`）

---

# 第 4 课 · costmap（预告）

**一句话**：全局 costmap 看整张地图做规划，局部 costmap 看车周围几米做实时避障。

待展开：
- costmap 的层（static / obstacle / inflation）
- `inflation_radius` 怎么定（本项目踩过：默认 0.55 把 4×4 房间堵死）
- 为什么“规划出路径但车不动”（局部 costmap 里有障碍）

---

# 第 5 课 · Nav2 的五个角色（预告）

| 角色 | 职责 |
|---|---|
| `planner_server` | 全局路径 |
| `controller_server` | 跟路径算速度 + 到达判定 |
| `behavior_server` | 恢复行为（后退、旋转） |
| `bt_navigator` | 行为树调度 |
| `lifecycle_manager` | 管理上面这些的生命周期 |

待展开：行为树的执行顺序、为什么 `Failed to make progress` 会 abort。

---

# 第 6 课 · TF 的时间戳（预告）

**一句话**：TF 不只是坐标，还带时间；过期的 TF 会让上层“基于旧世界”做决策。

待展开：
- 本项目踩过的坑：AMCL `update_min_d=0.25` 导致车静止时 `map→odom` 时间戳变旧 → controller 误判到达
- `transform_tolerance` 是什么

---

# 第 7 课 · QoS（预告）

**一句话**：不匹配时 DDS 静默失败，所以“话题有数据但我收不到”第一件事是 `ros2 topic info -v`。

待展开：Reliability / Durability / Depth、兼容表、传感器为什么用 BEST_EFFORT。

---

# 第 8 课 · Topic / Service / Action（预告）

| | Topic | Service | Action |
|---|---|---|---|
| 方向 | 广播 | 请求-应答 | 请求-应答 + 反馈 |
| 阻塞 | 不等 | 阻塞等结果 | 不阻塞，回调 |
| 可取消 | 无 | 无 | 有 |
| 用在 | 传感器、速度 | 瞬时操作 | 长任务（导航） |

---

# 附：一张图记住全部

```
                     ┌─ map（全局，会跳）
                     │    ↑ SLAM/AMCL 发 map→odom
                     │
   定位 ←────────────┤
                     │
                     └─ odom（连续，会漂）
                          ↑ 底盘驱动发 odom→base
                          │
                        base_link（车体）
                          ├─ laser_frame ──► /scan
                          ├─ imu_link ─────► /imu
                          └─ 轮子

建图：SLAM 用 /scan + odom，建出 /map，同时发 map→odom
导航：AMCL 用 /scan + /map + odom，修正 map→odom
      planner 用 map + costmap 出路径
      controller 用 odom + 局部 costmap 出 /cmd_vel
```
