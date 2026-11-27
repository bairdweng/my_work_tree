#!/usr/bin/env bash
# 把仓库 .skills/ 下的技能安装到本机豆包技能目录
#   - 只处理本仓库拥有的技能，绝不碰其他名字的技能
#   - 同名技能若由本仓库安装过，整体覆盖（工程版本为准）
#   - 同名技能若不是本仓库装的（本机原有/别的项目），默认跳过，需 --force 才覆盖
#   - 工程里删掉的技能，本机保留，需手动删除
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/.skills"
MARKER=".installed-by"
FORCE=no
[[ "${1:-}" == "--force" ]] && FORCE=yes

TARGET="${DOUBAO_USER_SKILLS:-}"
if [[ -z "$TARGET" ]]; then
  for c in \
    "$HOME/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace/.user_skills" \
    "$HOME/Library/Application Support/Doubao/Default/.doubao/agent_mode/workspace/.skills"
  do
    [[ -d "$c" ]] && { TARGET="$c"; break; }
  done
fi

if [[ -z "${TARGET:-}" || ! -d "$TARGET" ]]; then
  echo "[跳过] 没找到本机豆包技能目录"
  echo "       可用 DOUBAO_USER_SKILLS=<技能目录> ./install-skills.sh 指定"
  exit 0
fi

if [[ ! -d "$SRC" ]]; then
  echo "[跳过] 工程里没有 .skills 目录"
  exit 0
fi

ask_twice() {
  local q1="$1" q2="$2"
  printf '%s [y/N] ' "$q1"; read -r a || return 1
  [[ "$a" == "y" || "$a" == "Y" ]] || { echo "已取消，本机技能未改动"; return 1; }
  printf '%s [y/N] ' "$q2"; read -r b || return 1
  [[ "$b" == "y" || "$b" == "Y" ]] || { echo "已取消，本机技能未改动"; return 1; }
  return 0
}

if [[ "${SKILL_SYNC_YES:-0}" != "1" ]]; then
  n_ready=0
  for d in "$SRC"/*/; do [[ -f "$d/SKILL.md" ]] && n_ready=$((n_ready + 1)); done
  ask_twice "确认把工程里 ${n_ready} 个技能安装到本机 ${TARGET} ?" \
            "再次确认：本机同名技能副本会被整体覆盖" || exit 0
fi

updated=0; skipped=0
for d in "$SRC"/*/; do
  [[ -d "$d" ]] || continue
  name="$(basename "$d")"

  if [[ ! -f "$d/SKILL.md" ]]; then
    echo "  [跳过] ${name}：缺少 SKILL.md"
    continue
  fi

  dest="$TARGET/$name"
  if [[ -e "$dest" ]]; then
    owner=""
    [[ -f "$dest/$MARKER" ]] && owner="$(head -n1 "$dest/$MARKER")"
    if [[ "$owner" != "$ROOT" ]]; then
      if [[ "$FORCE" == yes ]]; then
        echo "  [覆盖] ${name}：本机同名技能归属「${owner:-未知/非本仓库}」，已按 --force 覆盖"
      else
        echo "  [跳过] ${name}：本机已有同名技能，且不是本仓库安装的（归属：${owner:-未知}）"
        echo "         确认要覆盖请执行 ./install-skills.sh --force"
        skipped=$((skipped + 1))
        continue
      fi
    fi
  fi

  mkdir -p "$dest"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude "$MARKER" "$d" "$dest/"
  else
    cp -R "$d". "$dest/"
  fi
  printf '%s\n' "$ROOT" >"$dest/$MARKER"
  echo "  已更新 $name"
  updated=$((updated + 1))
done

echo "[完成] 已同步 ${updated} 个技能到 ${TARGET}，跳过 ${skipped} 个"
echo "       新技能在下一轮会话才会出现在技能列表里"
