#!/usr/bin/env bash
# 只保留一份最新快照的双向同步（远端始终只有 1 个提交）
#   ./sync.sh up    本地 -> Git
#   ./sync.sh down  Git -> 本地
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")" || exit 1

REMOTE=origin
BRANCH="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo main)"
MODE="${1:-}"

say() { printf '%s\n' "$*"; }
note() { printf '  %s\n' "$*"; }

usage() {
  say "用法:"
  say "  ./sync.sh up     本地 -> Git（压成单个提交后强推）"
  say "  ./sync.sh down   Git -> 本地（对齐远端最新快照）"
  exit 1
}

confirm() {
  printf '%s [y/N] ' "$1"
  read -r ans || return 1
  [[ "$ans" == "y" || "$ans" == "Y" ]]
}

# 写操作前连问两次，两次都答 y 才继续
confirm_twice() {
  local q1="$1" q2="$2"
  confirm "$q1" || { say "已取消"; return 1; }
  confirm "$q2" || { say "已取消"; return 1; }
  return 0
}

[[ "$MODE" == "up" || "$MODE" == "down" ]] || usage

git rev-parse --git-dir >/dev/null 2>&1 || { say "当前目录不是 git 仓库"; exit 1; }
git remote get-url "$REMOTE" >/dev/null 2>&1 || { say "没有配置远端 $REMOTE"; exit 1; }

say "[检查] 获取远端状态 ..."
git fetch --quiet "$REMOTE" "+refs/heads/*:refs/remotes/$REMOTE/*" 2>/dev/null || {
  say "拉取远端信息失败：检查网络、SSH key 或远端地址"; exit 1;
}

REMOTE_OK=no; git rev-parse --verify --quiet "$REMOTE/$BRANCH" >/dev/null && REMOTE_OK=yes
LOCAL_OK=no;  git rev-parse --verify --quiet HEAD >/dev/null && LOCAL_OK=yes

slim() {
  git reflog expire --expire=now --all >/dev/null 2>&1
  git gc --prune=now --quiet >/dev/null 2>&1
}

# ---------------- 本地 -> Git ----------------
if [[ "$MODE" == up ]]; then
  # 先把明文 data/ 加密打包，仓库只存加密包；取消对明文目录的跟踪
  ./vault.sh pack || exit 1
  git rm -r --cached data --quiet 2>/dev/null || true
  git add -A
  TREE="$(git write-tree)" || { say "生成文件快照失败"; exit 1; }

  if [[ "$REMOTE_OK" == yes ]]; then
    if [[ "$TREE" == "$(git rev-parse "$REMOTE/$BRANCH^{tree}")" ]]; then
      git reset --quiet --hard "$REMOTE/$BRANCH"
      say "[完成] 与远端快照一致，无改动"
      exit 0
    fi

    # 远端自上次同步后被动过，或者本地从未同步过，覆盖前提示风险
    if [[ "$LOCAL_OK" == no ]]; then
      say "[提示] 远端已有快照，本地还没同步过，直接上传会覆盖远端内容"
    elif [[ "$(git rev-parse HEAD)" != "$(git rev-parse "$REMOTE/$BRANCH")" ]]; then
      say "[提示] 远端上次同步后有别人的更新，直接上传会覆盖掉它"
    fi
  fi

  confirm_twice \
    "确认把当前文件上传到远端 $REMOTE/$BRANCH ?" \
    "再次确认：远端快照会被整体替换，且不保留历史" || { say "已取消，未改动远端"; exit 0; }

  # 无父提交：每次都从当前文件生成一条全新的根提交，历史永远只有 1 条
  NEW="$(git commit-tree "$TREE" -m "snapshot: $(date '+%Y-%m-%d %H:%M')")" || { say "创建快照失败"; exit 1; }
  git update-ref -m "snapshot sync" "refs/heads/$BRANCH" "$NEW"
  git reset --quiet --hard "$NEW"

  if [[ "$REMOTE_OK" == yes ]]; then
    git push --force "$REMOTE" "$BRANCH" -q && { slim; say "[完成] 已用本地快照覆盖远端，仍只有 1 个提交"; exit 0; }
  else
    git push -u "$REMOTE" "$BRANCH" -q && { slim; say "[完成] 已推送首个快照"; exit 0; }
  fi
  say "推送失败"; exit 1
fi

# ---------------- Git -> 本地 ----------------
if [[ "$REMOTE_OK" == no ]]; then
  say "[提示] 远端还没有 $BRANCH 分支，先执行 ./sync.sh up"
  exit 1
fi

DIRTY=no; [[ -n "$(git status --porcelain)" ]] && DIRTY=yes
EXTRA=0
[[ "$LOCAL_OK" == yes ]] && EXTRA="$(git rev-list --count "$REMOTE/$BRANCH"..HEAD 2>/dev/null || echo 0)"

if [[ "$DIRTY" == yes || "$EXTRA" != "0" ]]; then
  say "[提示] 本地有新东西会被远端覆盖：未提交改动=${DIRTY}，本地独有提交=${EXTRA}"
fi

confirm_twice \
  "确认从远端 $REMOTE/$BRANCH 更新本地 ?" \
  "再次确认：本地未提交的改动和未推送内容会被丢弃" || { say "已取消，本地未改动"; exit 0; }

install_skills() {
  [[ -x "$(dirname "${BASH_SOURCE[0]}")/install-skills.sh" ]] || return 0
  SKILL_SYNC_YES=1 "$(dirname "${BASH_SOURCE[0]}")/install-skills.sh"
}

git reset --hard --quiet "$REMOTE/$BRANCH" && {
  slim
  say "[完成] 本地已对齐远端最新快照"
  install_skills
  # 解密还原明文 data/（需手动输入密码）
  ./vault.sh unpack || exit 1
  exit 0
}
say "覆盖失败"; exit 1
