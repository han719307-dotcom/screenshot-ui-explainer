#!/usr/bin/env python3
"""
annotate_png.py - 把编号圆点画到截图上，右侧拼一块分组的图例面板，
产出一张自包含的"标注图" PNG。

用法：
    python annotate_png.py annotations.json -o 标注图.png [--theme dark|light]

annotations.json 格式（列表）：
[
  {
    "n": 1,                    # 编号（必填，唯一）
    "x": 44, "y": 41,          # 原图像素坐标（必填）—— 圆点圆心
    "group": "顶部导航栏",      # 分组名（必填，决定图例分区）
    "title": "汉堡菜单（☰）",    # 条目名（必填）
    "desc": "收起/展开左侧导航栏。"  # 说明（可选，仅 HTML 版展示）
  }
]

可选字段：
    "label_x"/"label_y"  不填则用 x/y

设计要点（踩过坑）：
- 圆点不要压住文字，压在空白处或元素正上方/正下方；小图标按钮尽量落在元素内部空白。
- 图例面板用与截图同色系的背景，视觉上是一张图；浅色主题自动切换配色。
- 字号不要太小，导出后缩放仍要清晰；编号为两位数字时圆点半径要留余量。
"""

import argparse
import json
import sys
from pathlib import Path

# 各平台常见中文字体，按优先级探测；找不到时回退到 Pillow 内置位图字体并告警。
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def pick_font(explicit=None):
    """返回可用的中文字体路径；explicit 优先，其次按平台候选表探测。"""
    if explicit and Path(explicit).exists():
        return explicit
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def wrap_text(draw, text, font, max_width):
    """按像素宽度折行，中英文混排都能处理；超长无空格的串按字符硬切。"""
    if not text:
        return []
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def collect_groups(data):
    """把标注按 group 归并，并从可选的 groups 元信息里取出每个分组的用途说明。

    返回 [(组名, 组用途说明或 None, [条目...]), ...]
    分组用途说明有两种写法（都支持）：
      1. 顶层 "group_notes": {"顶部导航栏": "整个页面的全局入口区……"}
      2. 顶层 "groups": [{"name": "顶部导航栏", "note": "……"}]
    """
    notes = {}
    if isinstance(data, dict):
        for k, v in (data.get("group_notes") or {}).items():
            notes[k] = v
        for g in (data.get("groups") or []):
            if isinstance(g, dict) and g.get("name"):
                notes[g["name"]] = g.get("note", notes.get(g["name"]))

    items = data["annotations"] if isinstance(data, dict) else data
    order, grouped = [], {}
    for a in items:
        g = a.get("group", "其他")
        if g not in grouped:
            grouped[g] = []
            order.append(g)
        grouped[g].append(a)
    return [(g, notes.get(g), grouped[g]) for g in order]


def main():
    ap = argparse.ArgumentParser(description="生成带编号与图例的标注图 PNG")
    ap.add_argument("annotations", help="annotations.json 路径")
    ap.add_argument("-i", "--image", default=None,
                    help="原图路径；不填则读取 annotations.json 同目录下的 source 字段或 github-dashboard 约定")
    ap.add_argument("-o", "--output", default="annotated.png", help="输出 PNG 路径")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--panel-width", type=int, default=620, help="右侧图例带宽，默认 620")
    ap.add_argument("--font", default=None, help="常规字体路径，默认自动探测中文字体")
    ap.add_argument("--font-bold", default=None, help="粗体字体路径，默认自动探测中文字体")
    ap.add_argument("--no-panel", action="store_true", help="只画编号，不拼图例面板")
    args = ap.parse_args()

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        sys.exit("需要 Pillow：pip install pillow")

    src = Path(args.annotations)
    data = json.loads(src.read_text(encoding="utf-8"))
    items = data["annotations"] if isinstance(data, dict) else data
    image_path = args.image or (data.get("source") if isinstance(data, dict) else None)
    if not image_path:
        sys.exit("请用 -i 指定原图路径，或在 JSON 顶层提供 source 字段")

    if args.theme == "dark":
        BG, FG, GRP, GREY, DOT, DOT_EDGE = (
            (13, 17, 23), (230, 237, 243), (88, 166, 255),
            (139, 148, 158), (240, 68, 56), (255, 255, 255))
    else:
        BG, FG, GRP, GREY, DOT, DOT_EDGE = (
            (255, 255, 255), (31, 35, 40), (11, 87, 208),
            (89, 99, 110), (240, 68, 56), (255, 255, 255))

    im = Image.open(image_path).convert("RGB")
    W, H = im.size

    font_path = pick_font(args.font)
    bold_path = pick_font(args.font_bold) or font_path
    if font_path:
        F_BADGE = ImageFont.truetype(bold_path, 17)
        F_HEAD = ImageFont.truetype(bold_path, 26)
        F_GRP = ImageFont.truetype(bold_path, 19)
        F_ITEM = ImageFont.truetype(font_path, 17)
        F_SUB = ImageFont.truetype(font_path, 16)
        F_NOTE = ImageFont.truetype(font_path, 15)
    else:
        print("警告：未找到中文字体，回退到 Pillow 内置字体，中文可能显示为方块。\n"
              "      请用 --font / --font-bold 指定字体文件。", file=sys.stderr)
        F_BADGE = ImageFont.load_default(17)
        F_HEAD = ImageFont.load_default(26)
        F_GRP = ImageFont.load_default(19)
        F_ITEM = ImageFont.load_default(17)
        F_SUB = ImageFont.load_default(16)
        F_NOTE = ImageFont.load_default(15)

    # ---------- 图例分组（含每个分组的用途说明） ----------
    groups = collect_groups(data)
    sub_text = data.get("subtitle") if isinstance(data, dict) else None

    TITLE_H, SUB_H, FOOT = 40, 26, 20   # 标题占位 / 副标题占位 / 底部留白
    ITEM_H, GROUP_H = 34, 42
    NOTE_LH, NOTE_GAP = 24, 10           # 分组说明行高 / 与首条之间的间距

    NOTE_W = args.panel_width - 60       # 说明文字可用宽度

    # 预折行，后续算高度和绘制都用同一份结果，避免不一致
    from PIL import ImageDraw as _ID
    _ruler = _ID.Draw(Image.new("RGB", (1, 1)))
    notes_wrapped = {g: wrap_text(_ruler, note, F_NOTE, NOTE_W) for g, note, _ in groups if note}

    def group_block_h(name, note):
        n_items = next(len(it) for g, _, it in groups if g == name)
        h = GROUP_H + ITEM_H * n_items
        if notes_wrapped.get(name):
            h += NOTE_LH * len(notes_wrapped[name]) + NOTE_GAP
        return h

    def HEAD_BASE():
        return TITLE_H + (SUB_H if sub_text else 0) + 26

    legend_h = (HEAD_BASE()
                + sum(group_block_h(g, note) for g, note, _ in groups)
                + FOOT)
    CH = max(H, legend_h)

    if args.no_panel:
        canvas = im.copy()
        base_x = 0
        CH = H
    else:
        canvas = Image.new("RGB", (W + args.panel_width, CH), BG)
        canvas.paste(im, (0, 0))
        base_x = W

    d = ImageDraw.Draw(canvas)

    # ---------- 编号圆点 ----------
    for a in items:
        x, y = a.get("label_x", a["x"]), a.get("label_y", a["y"])
        r = 15 if len(str(a["n"])) < 2 else 16
        d.ellipse([x - r - 2, y - r - 2, x + r + 2, y + r + 2], fill=DOT_EDGE)
        d.ellipse([x - r, y - r, x + r, y + r], fill=DOT)
        t = str(a["n"])
        bb = d.textbbox((0, 0), t, font=F_BADGE)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - (bb[3] - bb[1]) / 2 - bb[1]),
               t, font=F_BADGE, fill=(255, 255, 255))

    if args.no_panel:
        canvas.save(args.output)
        print(f"{args.output}  {canvas.size}")
        return

    # ---------- 图例面板 ----------
    px = base_x + 30
    right = W + args.panel_width - 30
    title = data.get("title", "界面标注") if isinstance(data, dict) else "界面标注"
    d.text((px, 26), title, font=F_HEAD, fill=FG)
    sub = sub_text
    if sub:
        d.text((px, 26 + TITLE_H), sub, font=F_SUB, fill=GREY)
    head_line = 26 + TITLE_H + (SUB_H if sub else 0)
    d.line([(px, head_line), (right, head_line)], fill=GRP, width=2)

    y = head_line + 18
    for gname, note, gitems in groups:
        d.text((px, y), gname, font=F_GRP, fill=GRP)
        y += GROUP_H - 6

        # 分组用途说明：先讲清楚"这块地方是干什么用的"，再列具体控件
        for ln in notes_wrapped.get(gname, []):
            d.text((px, y), ln, font=F_NOTE, fill=GREY)
            y += NOTE_LH
        if notes_wrapped.get(gname):
            y += NOTE_GAP

        for a in gitems:
            d.ellipse([px, y + 2, px + 19, y + 21], fill=DOT)
            t = str(a["n"])
            bb = d.textbbox((0, 0), t, font=F_BADGE)
            d.text((px + 9.5 - (bb[2] - bb[0]) / 2 - bb[0],
                    y + 11.5 - (bb[3] - bb[1]) / 2 - bb[1]), t, font=F_BADGE, fill=(255, 255, 255))
            d.text((px + 28, y), a["title"], font=F_ITEM, fill=FG)
            y += ITEM_H
        y += 8

    canvas.save(args.output)
    print(f"{args.output}  {canvas.size}")


if __name__ == "__main__":
    main()
