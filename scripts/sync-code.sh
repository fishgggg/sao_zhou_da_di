#!/usr/bin/env bash
# 从 WSL 工作区同步代码到本仓库的 sim_ws/ 镜像目录
#
# 方向：单向。永远以 WSL 的 ~/xuegecar_sim_ws 为准。
# 用法：bash scripts/sync-code.sh
#
# 为什么是镜像而不是主副本：ROS 2 的 colcon build 必须在 Linux 文件系统上跑
# （/mnt/d 上会慢一个数量级，且会丢可执行权限位）。GitHub 上的代码用于展示、
# 备份和跨机迁移，构建永远在 WSL ext4 上进行。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WSL_WS="${WSL_WS:-~/xuegecar_sim_ws}"

echo "同步 ${WSL_WS} → ${REPO_ROOT}/sim_ws"

mkdir -p "${REPO_ROOT}/sim_ws"

timeout 120 wsl -e bash -lc "cd ${WSL_WS} && tar cf - \
  --exclude=./build --exclude=./install --exclude=./log --exclude=./.git \
  src .gitignore" | tar xf - -C "${REPO_ROOT}/sim_ws"

COUNT=$(find "${REPO_ROOT}/sim_ws" -type f | wc -l | tr -d ' ')
echo "完成：${COUNT} 个文件"

if command -v git >/dev/null 2>&1; then
  echo "--- git status（sim_ws） ---"
  git -C "${REPO_ROOT}" status --short -- sim_ws || true
fi
