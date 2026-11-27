---
name: image-watermark
description: 给商品图 / 实拍图批量加平铺斜向文字水印时使用。触发场景：用户说"批量加水印""图片防盗图""铺水印""给图片打水印"，或要调整水印文字、透明度、间距、角度。基于 Python Pillow，脚本在 scripts/watermark.py；不覆盖原图，成品输出独立目录。
---

# image-watermark 批量平铺水印

## 适用范围

固定域：**商品图、实拍图、Listing 配图**的批量文字水印（斜向平铺）。单张预览、目录批量均可。

不做：图片裁切、调色、修图、AI 重绘、Logo 合成；这些不在本技能范围内。

## 依赖

- Python 3，依赖 **Pillow**：

```bash
pip3 install pillow
```

- 字体按平台自动兜底（macOS 苹方 / 黑体、Windows 微软雅黑、Linux Noto CJK）；缺中文字体时用 `--font` 指定字体文件路径。

## 脚本

`scripts/watermark.py`，跨平台，不写死本机路径。

### 快速用法

单张预览：

```bash
python3 scripts/watermark.py -i 图.jpg --text "水印文字"
```

整个目录批量：

```bash
python3 scripts/watermark.py -i ./images -o ./images/watermarked --text "水印文字"
```

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `-i / --input` | 必填 | 图片文件或目录 |
| `-o / --output` | `<输入目录>/watermarked` | 输出目录，不覆盖原图 |
| `--text` | 必填 | 水印文字 |
| `--font` | 自动兜底 | 字体文件路径 |
| `--font-size` | 28 | 字号 |
| `--alpha` | 60 | 不透明度 0–255，越大越实 |
| `--angle` | 30 | 倾斜角度 |
| `--gap-x` | 320 | 水平间距（像素），越大越疏 |
| `--gap-y` | 170 | 垂直间距（像素） |
| `--color` | `120,120,120` | 颜色 R,G,B |
| `--quality` | 92 | JPEG 质量 |

## 工作规则

1. **不覆盖原图**：成品一律输出到独立目录；原图留在原处不动。
2. **先预览一张**：批量前先挑一张出样，确认文字、深浅、间距不压商品关键细节，再跑全量。
3. **改动需授权**：水印文字、位置、透明度等参数按用户确认值执行；不擅自对图片做裁切、调色等其它处理。
4. **背景适配**：深色背景可用偏白水印（如 `255,255,255`），浅色背景用深灰；预览时两种背景都看一眼。
5. 支持 jpg / jpeg / png / webp；PNG 保留透明通道。

## 其它电脑使用

- 整个 `image-watermark/` 目录随仓库 `.skills/` 同步；新机器装好 Python 和 Pillow 即可调用脚本。
- 若本机技能目录由安装脚本管理，运行仓库根目录的 `./install-skills.sh` 同步技能副本。
