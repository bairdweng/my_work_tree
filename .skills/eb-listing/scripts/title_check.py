#!/usr/bin/env python3
"""eBay 标题体检：字符数、超限、无效词、全大写、核心词位置。

用法：
    python3 title_check.py "Title One" "Title Two"
    printf 'Title A\nTitle B\n' | python3 title_check.py
"""
import re
import sys

LIMIT = 80
BAD_WORDS = [
    "best", "hot", "sale", "free shipping", "top", "new arrival",
    "100%", "guaranteed", "cheap", "wholesale",
    "look", "wow", "buy now", "limited time",
]
# 涉及品牌权利归属的表述，一律不写
CLAIM_WORDS = ["genuine", "oem", "original", "authentic", "replacement for", "official"]
BRANDS = ["traxxas", "axial", "scx", "trx", "hpi", "losi", "arrma"]
COLOR_WORDS = ["black", "red", "silver", "white", "blue", "green", "gray", "grey", "orange", "gold"]
US_SPELLING = {"tyre": "tire", "aluminium": "aluminum", "colour": "color", "metre": "meter"}


def check(title):
    problems = []
    n = len(title)

    if n > LIMIT:
        problems.append(f"超限 {n - LIMIT} 字符（上限 {LIMIT}）")
    if title != title.strip():
        problems.append("首尾有空白")
    if re.search(r"\s{2,}", title):
        problems.append("存在连续空格")

    low = title.lower()
    for w in BAD_WORDS:
        if w in low:
            problems.append(f"无效词：{w}")
    for w in CLAIM_WORDS:
        if w in low:
            problems.append(f"权利风险词：{w}（只写 for / Compatible with）")
    for w in COLOR_WORDS:
        if re.search(rf"\b{w}\b", low):
            problems.append(f"标题不含颜色：{w}（颜色放 Item Specifics）")
    for uk, us in US_SPELLING.items():
        if re.search(rf"\b{uk}\b", low):
            problems.append(f"非美式拼写：{uk} → {us}")

    if re.search(r"!{2,}", title):
        problems.append("连续感叹号")

    # 全大写单词（3 个字母以上、不含数字、且不是常见缩写/车型代号）
    allow = {"ABS", "PVC", "USB", "LED", "RC", "SCX", "TRX", "KV", "ESC", "BEC", "CNC", "PVD", "TPU"}
    caps = [t for t in title.split()
            if t.isupper() and len(t) >= 3 and not re.search(r"\d", t) and t not in allow]
    if caps:
        problems.append("全大写词：" + "、".join(caps))

    # 首词不能是车型代号或品牌词，否则像在宣称自己是该品牌产品
    first = re.sub(r"[^A-Za-z0-9/]", "", title.split()[0]).lower() if title.split() else ""
    if first in BRANDS or re.match(r"^[a-z]{2,}\d", first):
        problems.append("标题以车型/品牌词开头，容易被当作品牌宣称，首词应用品类词")

    # 出现车型代号时，必须有兼容表述
    has_model = any(b in low for b in ("scx", "trx", "arrma", "losi", "traxxas"))
    if has_model and " for " not in f" {low} " and "compatible" not in low:
        problems.append("含车型代号但缺少 for / Compatible with 兼容表述")

    return n, problems


def main():
    titles = sys.argv[1:]
    if not titles:
        titles = [line.strip() for line in sys.stdin if line.strip()]

    if not titles:
        print("没有输入标题")
        return 1

    bad = 0
    for t in titles:
        n, problems = check(t)
        if problems:
            bad += 1
            print(f"[{n} 字符] {t}")
            for p in problems:
                print(f"    ✗ {p}")
        else:
            print(f"[{n} 字符] {t}\n    ✓ 通过")

    print(f"\n合计 {len(titles)} 条，{bad} 条需要修改")
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
