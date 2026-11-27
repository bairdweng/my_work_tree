#!/usr/bin/env bash
# data/ 明文不入库；仓库只存加密包 data.enc.tar.gz（AES-256-CBC + PBKDF2）
#
#   ./vault.sh pack      输密码 → 打包加密 data/ → data.enc.tar.gz
#   ./vault.sh unpack    输密码 → 解密还原 data/
#
# 密码不写入脚本、不进仓库；pack / unpack 都手动输入。
# 密码丢失则加密包无法还原，请自行妥善保管。

set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

ENC="data.enc.tar.gz"
TMP_TAR="data.tar.tmp"
RESTORE_TAR="data.restore.tar"
ITER=100000

err() { printf '%s\n' "$*" >&2; }

pack() {
  [ -d data ] || { err "本地无 data/ 目录，无需打包"; exit 1; }

  local p1 p2
  read -s -r -p "输入加密密码：" p1; echo
  read -s -r -p "再输一次确认：" p2; echo
  [ "$p1" == "$p2" ] || { err "两次密码不一致，已取消"; exit 1; }

  tar -czf "$TMP_TAR" -C data . || { err "打包失败"; exit 1; }
  VAULT_PASS="$p1" openssl enc -aes-256-cbc -pbkdf2 -iter "$ITER" -salt \
    -in "$TMP_TAR" -out "$ENC" -pass env:VAULT_PASS \
    || { err "加密失败"; rm -f "$TMP_TAR"; exit 1; }
  rm -f "$TMP_TAR"
  err "已生成加密包 ${ENC}（明文 data/ 不入库）"
}

unpack() {
  [ -f "${ENC}" ] || { err "仓库无加密包 ${ENC}"; exit 1; }

  local p1
  read -s -r -p "输入解密密码：" p1; echo

  VAULT_PASS="$p1" openssl enc -d -aes-256-cbc -pbkdf2 -iter "$ITER" \
    -in "$ENC" -out "$RESTORE_TAR" -pass env:VAULT_PASS \
    || { err "密码错误或加密包损坏，解密失败，本地 data/ 未改动"; rm -f "$RESTORE_TAR"; exit 1; }

  # 先校验压缩包完整性，通过后再清本地 data/，避免坏包毁掉现有素材
  tar -tzf "$RESTORE_TAR" >/dev/null \
    || { err "解密包校验失败，本地 data/ 未改动"; rm -f "$RESTORE_TAR"; exit 1; }

  rm -rf data && mkdir data
  tar -xzf "$RESTORE_TAR" -C data || { err "解压失败"; rm -f "$RESTORE_TAR"; exit 1; }
  rm -f "$RESTORE_TAR"
  err "已还原 data/"
}

case "${1:-}" in
  pack) pack ;;
  unpack) unpack ;;
  *) err "用法: ./vault.sh pack | unpack"; exit 1 ;;
esac
