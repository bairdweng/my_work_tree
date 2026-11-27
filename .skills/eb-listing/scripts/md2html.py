#!/usr/bin/env python3
"""把 listing.md 里的「描述」小节转成 eBay 可用的安全 HTML。

只输出 <p> <ul> <li> <strong> <br>，不含样式、表格、图片、链接。
用法：python3 md2html.py <listing.md> > description.html
"""
import html
import re
import sys

SAFE = re.compile(r"<(p|ul|li|strong|br|/p|/ul|/li|/strong)>")


def extract(text):
    m = re.search(r"^##\s*描述.*?$(.*?)(?=^##\s|\Z)", text, re.S | re.M)
    return m.group(1) if m else None


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def convert(md):
    out, in_list = [], False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            close_list()
            continue

        if line.startswith("###") or line.startswith("##") or line.startswith("#"):
            close_list()
            title = line.lstrip("#").strip()
            out.append(f"<p><strong>{inline(title)}</strong></p>")
            continue

        if re.match(r"^\s*[-*]\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(re.sub(r'^\s*[-*]\s+', '', line))}</li>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(re.sub(r'^\s*\d+\.\s+', '', line))}</li>")
            continue

        close_list()
        out.append(f"<p>{inline(line)}</p>")

    close_list()
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 md2html.py <listing.md>")
        return 1
    body = extract(open(sys.argv[1], encoding="utf-8").read())
    if body is None:
        print("没找到「## 描述」小节")
        return 1
    result = convert(body)
    if SAFE.search(re.sub(r"<(p|ul|li|strong|br|/p|/ul|/li|/strong)>", "", result)):
        print("检测到非白名单标签", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
