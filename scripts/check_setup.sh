#!/usr/bin/env bash
# gbro-collage-broll environment self-check (MiniMax H3 pipeline).
# Exit 0 = all good; exit 1 = at least one item missing (details on stdout).

set -u

FAIL=0

ok()   { printf 'PASS  %s\n' "$1"; }
bad()  { printf 'FAIL  %s\n' "$1"; FAIL=1; }

# 1. MINIMAX_API_KEY（环境变量优先，回退读取 skill 目录下的 .env）
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -z "${MINIMAX_API_KEY:-}" ] && [ -f "$SKILL_DIR/.env" ]; then
  MINIMAX_API_KEY="$(grep -E '^MINIMAX_API_KEY=' "$SKILL_DIR/.env" | head -1 | cut -d= -f2-)"
fi
if [ -n "${MINIMAX_API_KEY:-}" ]; then
  ok "MINIMAX_API_KEY 已设置"
else
  bad "MINIMAX_API_KEY 未设置（到 MiniMax 开放平台创建：https://platform.minimaxi.com/user-center/basic-information/interface-key ，创建后写入 $SKILL_DIR/.env 或 export 到 shell 配置；并确认已开通 H3 按量付费）"
fi

# 2. ffmpeg / ffprobe
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  ok "ffmpeg / ffprobe 可用"
else
  bad "ffmpeg / ffprobe 缺失（macOS: brew install ffmpeg；Debian/Ubuntu: sudo apt install ffmpeg）"
fi

# 3. Python >= 3.10（视频脚本只用标准库，无需第三方依赖）
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  ok "python3 >= 3.10"
else
  bad "python3 缺失或版本低于 3.10"
fi

exit $FAIL
