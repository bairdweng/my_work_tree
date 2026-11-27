#!/usr/bin/env python3
"""eBay 描述体检：长度、禁用表述、外链、联系方式、段落长度。

用法：
    python3 desc_check.py ../../../../data/rc/eb/scx30-trailer/listing.md
"""
import re
import sys

MAX_WORDS = 250          # 默认短版上限，成套复杂件可放宽到 450
MAX_PARAGRAPH_LINES = 4  # 单段连续行数
BAD_PHRASES = [
    "lifetime warranty", "100% satisfaction", "money back guarantee",
    "best on the market", "world's best", "free gift", "gift",
    "official", "genuine", "oem", "replacement for",
]
SHIP_WORDS = ["shipping", "freight", "delivery time", "returns policy"]


def extract_section(text, title="描述"):
    m = re.search(rf"^##\s*{re.escape(title)}.*?$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    return m.group(1) if m else None


def check(body):
    problems = []
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-']*", body)
    if len(words) > MAX_WORDS:
        problems.append(f"超过默认长度：{len(words)} 词（上限 {MAX_WORDS}，成套复杂件可到 450）")

    low = body.lower()
    for p in BAD_PHRASES:
        if p in low:
            problems.append(f"不可承诺表述：{p}")
    if re.search(r"https?://|www\.", low):
        problems.append("含外链，eBay 禁止站外引导")
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", body):
        problems.append("含邮箱，禁止放联系方式")
    if re.search(r"\b(?:\+?\d[\d\-\s]{7,})\b", body):
        problems.append("含疑似电话号码")
    for w in SHIP_WORDS:
        if w in low:
            problems.append(f"描述里不写运输/售后：{w}（按约定留空）")

    # 连续行过多，手机端会变成一堵墙
    run = 0
    for line in body.splitlines():
        if line.strip():
            run += 1
            if run > MAX_PARAGRAPH_LINES:
                problems.append("存在超过 4 行的连续段落，建议分块")
                break
        else:
            run = 0

    return len(words), problems


def main():
    if len(sys.argv) < 2:
        print("用法: python3 desc_check.py <listing.md>")
        return 1
    text = open(sys.argv[1], encoding="utf-8").read()
    body = extract_section(text)
    if body is None:
        print("没找到「## 描述」小节")
        return 1

    n, problems = check(body)
    if problems:
        print(f"[{n} 词] 需要修改：")
        for p in problems:
            print(f"    ✗ {p}")
        return 2

    print(f"[{n} 词] ✓ 通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
