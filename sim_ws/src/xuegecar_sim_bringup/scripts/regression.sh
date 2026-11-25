#!/bin/bash
# 回归验收脚本：一条命令验证阶段 8-9 的关键能力还在不在。
#
# 用法：
#   bash regression.sh                    # 默认用假底盘（sim:=false，约 40 秒）
#   bash regression.sh --sim              # 用 Gazebo（慢，约 90 秒，需要 gazebo 可用）
#
# 设计原则：
#   - 每一步都独立判定，失败不中断（这样一次能看到所有问题）
#   - 只用 ros2 CLI + 超时，不依赖额外 Python 包
#   - 结束时一定清理，不留孤儿进程

# 注意：不能用 set -u —— ROS 的 setup.bash 里有未定义变量，会直接中断
SIM_ARG="sim:=false"
GRACE="3.0"
if [ "${1:-}" = "--sim" ]; then
  SIM_ARG="sim:=true"
  GRACE="25.0"
fi

source /opt/ros/humble/setup.bash
source "$HOME/xuegecar_sim_ws/install/setup.bash"

# WSL 下 Fast DDS 的共享内存端口容易和残留进程抢锁（表现为
# "Failed init_port fastrtps_portXXXX: open_and_lock_file failed"），
# 强制走 UDP 可以完全避开。
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4

PASS=0
FAIL=0
LAUNCH_PID=""

say() { echo; echo "=== $* ==="; }

check() {  # $1=名称 $2=实际 $3=期望
  if [ "$2" = "$3" ]; then
    echo "[PASS] $1"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $1   实际=[$2] 期望=[$3]"
    FAIL=$((FAIL + 1))
  fi
}

# 数值比较：$1=名称 $2=实际 $3=阈值 $4=gt/lt/ge
check_num() {
  local ok
  ok=$(awk -v a="$2" -v b="$3" -v op="$4" 'BEGIN{
    if (a == "" || a == "---") { print "no"; exit }
    if (op == "gt")      print (a >  b) ? "yes" : "no";
    else if (op == "ge") print (a >= b) ? "yes" : "no";
    else                 print (a <  b) ? "yes" : "no";
  }')
  if [ "$ok" = "yes" ]; then
    echo "[PASS] $1   （$2 $4 $3）"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $1   实际=[$2] 要求 $4 $3"
    FAIL=$((FAIL + 1))
  fi
}

state() { timeout 6 ros2 topic echo /mission_state --once 2>/dev/null | head -1 | sed 's/data: //'; }
odomx() { timeout 6 ros2 topic echo /odom --once --field pose.pose.position.x 2>/dev/null | head -1; }
cmd()   { timeout 6 ros2 topic pub --once /mission_command std_msgs/msg/String "{data: $1}" >/dev/null 2>&1; }
vel()   { timeout 6 ros2 topic pub --once /cmd_vel_teleop geometry_msgs/msg/Twist "{linear: {x: $1}}" >/dev/null 2>&1; }
navvel(){ timeout 6 ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: $1}}" >/dev/null 2>&1; }

cleanup() {
  [ -n "$LAUNCH_PID" ] && kill "$LAUNCH_PID" 2>/dev/null
  pkill -f "component_containe[r]" 2>/dev/null
  pkill -f "xuegecar_sim_missio[n]" 2>/dev/null
  pkill -f "fake_chass[i]s" 2>/dev/null
  sleep 2
}
trap cleanup EXIT

say "0. 清理旧进程"
cleanup
sleep 2

say "1. 启动（$SIM_ARG, grace=$GRACE）"
ros2 launch xuegecar_sim_bringup bringup.launch.py \
  "$SIM_ARG" initial_state:=IDLE "grace_period:=$GRACE" > /tmp/regression_launch.log 2>&1 &
LAUNCH_PID=$!
sleep 8

say "2. 基础能力"
NODES=$(ros2 node list 2>/dev/null | wc -l)
check_num "节点数 >= 3" "$NODES" "3" "ge"
check "初始状态 IDLE" "$(state)" "IDLE"

say "3. 闸门：IDLE 不放行"
X0=$(odomx); vel 0.3; sleep 2; X1=$(odomx)
D=$(awk -v a="$X0" -v b="$X1" 'BEGIN{printf "%.3f", (b-a<0?-(b-a):b-a)}')
check_num "IDLE 下速度被拦（位移 < 0.02）" "$D" "0.02" "lt"

say "4. 迁移：IDLE → TELEOP"
cmd TELEOP
check "切到 TELEOP" "$(state)" "TELEOP"

say "5. 放行：TELEOP 下能动"
X0=$(odomx); vel 0.3; sleep 2
X1=$(odomx); vel 0.0; sleep 0.5
D=$(awk -v a="$X0" -v b="$X1" 'BEGIN{printf "%.3f", b-a}')
check_num "TELEOP 下位移 > 0.3" "$D" "0.3" "gt"

say "6. 分权：TELEOP 不吃 nav 源"
X0=$(odomx); navvel 0.5; sleep 2
X1=$(odomx); navvel 0.0; sleep 0.5
D=$(awk -v a="$X0" -v b="$X1" 'BEGIN{printf "%.3f", (b-a<0?-(b-a):b-a)}')
check_num "nav 源被拦（位移 < 0.02）" "$D" "0.02" "lt"

say "7. 急停"
cmd ESTOP
check "进入 ESTOP" "$(state)" "ESTOP"
X0=$(odomx); vel 0.5; sleep 2; X1=$(odomx)
D=$(awk -v a="$X0" -v b="$X1" 'BEGIN{printf "%.3f", (b-a<0?-(b-a):b-a)}')
check_num "ESTOP 压零速（位移 < 0.02）" "$D" "0.02" "lt"

say "8. 急停粘性"
cmd TELEOP
check "TELEOP 不能覆盖 ESTOP" "$(state)" "ESTOP"

say "9. 复位"
cmd RESET
check "RESET 回到 IDLE" "$(state)" "IDLE"

say "10. 看门狗（杀掉 fake_chassis，数据中断）"
CHASSIS_PID=$(pgrep -f "fake_chass[i]s" | head -1)
if [ -n "$CHASSIS_PID" ]; then
  cmd TELEOP
  sleep 1
  kill -9 "$CHASSIS_PID" 2>/dev/null
  sleep 3
  check "数据中断后进 ERROR" "$(state)" "ERROR"
  echo "[NOTE] 看门狗恢复需重启 fake_chassis 再 RESET，属 8.4 手工步骤，此处不验"
else
  echo "[SKIP] 找不到 fake_chassis 进程（sim:=true 模式下由插件提供 odom）"
fi

say "结果"
echo "通过 $PASS 项，失败 $FAIL 项"
[ "$FAIL" -eq 0 ] && echo "✅ 全部通过" || echo "❌ 有失败项，看上面 [FAIL] 行"
exit "$FAIL"
