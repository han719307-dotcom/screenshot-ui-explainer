#!/usr/bin/env python3
"""
make_social_preview.py - 生成 GitHub Social Preview（社交预览图）素材。

产物：docs/social-preview.png，尺寸 1280x640（GitHub 要求的 2:1）。

为什么单独做一张而不是直接传 demo-annotated.png：
标注图是给"仔细看"用的，缩到 1280x640 之后文字全部糊掉；
社交预览图只需要回答"这是干什么的"，所以放标题 + 一张界面缩略图即可。

用法：
    python docs/make_social_preview.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 640

BG = (13, 17, 23)           # 深底
WHITE = (240, 246, 252)     # 主标题
BLUE = (88, 166, 255)       # 强调
MUTED = (139, 148, 158)     # 说明文字
DIM = (110, 118, 129)       # 次要信息
BORDER = (48, 54, 61)       # 图片卡片描边
BADGE_BG = (31, 111, 235)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SHOT = REPO / "examples" / "output" / "demo-annotated.png"
OUT = HERE / "social-preview.png"

# 标注图里原始截图的区域（标注图画布会在右侧拼图例面板，并可能加高）
SHOT_BOX = (0, 0, 1600, 1000)

FONT_DIR = Path(r"C:\Windows\Fonts")
FALLBACK_DIRS = [
    FONT_DIR,
    Path("/System/Library/Fonts"),
    Path("/usr/share/fonts/opentype/noto"),
    Path("/usr/share/fonts/truetype/dejavu"),
]

# 名字要做拉丁字母和中文分开找：CJK 字体的拉丁字形偏窄，标题用西文字体更好看
CANDIDATES = {
    "display": ["segoeuib.ttf", "arialbd.ttf", "Helvetica.ttc", "NotoSans-Bold.ttf"],
    "body": ["segoeui.ttf", "arial.ttf", "Helvetica.ttc", "NotoSans-Regular.ttf"],
    "mono": ["consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"],
    "cjk": ["msyh.ttc", "PingFang.ttc", "NotoSansCJK-Regular.ttc"],
    "cjk_bold": ["msyhbd.ttc", "PingFang.ttc", "NotoSansCJK-Bold.ttc"],
    # 兜底：保证即使找不到西文字体也能出图
    "any": ["arial.ttf", "DejaVuSans.ttf"],
}


def load(kind, size):
    names = CANDIDATES.get(kind, [])
    for name in names + CANDIDATES["any"]:
        for d in FALLBACK_DIRS:
            p = d / name
            if p.exists():
                try:
                    return ImageFont.truetype(str(p), size)
                except OSError:
                    continue
    raise SystemExit("找不到可用字体，请安装 Arial / 微软雅黑 / Noto Sans")


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                        radius=radius, fill=255)
    return m


def main():
    if not SHOT.exists():
        raise SystemExit(
            f"缺少素材 {SHOT}\n"
            "请先跑 demo：\n"
            "  cd examples && python make_demo_shot.py\n"
            "  python ../scripts/annotate_png.py annotations.json "
            "-o output/demo-annotated.png --theme light"
        )

    f_badge = load("display", 15)
    f_title = load("display", 40)
    f_sub = load("cjk", 26)
    f_body = load("cjk", 17)
    f_item = load("cjk", 15)
    f_url = load("mono", 14)

    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    # ---------------- 右侧：界面缩略图 ----------------
    shot = Image.open(SHOT).convert("RGB")
    box = (0, 0, min(SHOT_BOX[2], shot.width), min(SHOT_BOX[3], shot.height))
    shot = shot.crop(box)

    card_w = 544
    card_h = round(card_w * shot.height / shot.width)
    shot = shot.resize((card_w, card_h), Image.LANCZOS)

    card_x, card_y = W - card_w - 56, (H - card_h) // 2
    im.paste(shot, (card_x, card_y), rounded_mask((card_w, card_h), 14))
    d.rounded_rectangle([card_x, card_y, card_x + card_w - 1, card_y + card_h - 1],
                        radius=14, outline=BORDER, width=1)

    # ---------------- 左侧：文字 ----------------
    x = 72
    y = 128

    # 徽标
    tw = d.textlength("AGENT SKILL", font=f_badge)
    d.rounded_rectangle([x, y, x + tw + 30, y + 32], radius=16, fill=BADGE_BG)
    d.text((x + 15, y + 16), "AGENT SKILL", font=f_badge, fill=(255, 255, 255), anchor="lm")
    y += 32 + 26

    d.text((x, y), "Screenshot UI Explainer", font=f_title, fill=WHITE, anchor="la")
    y += 40 + 14

    d.text((x, y), "界面截图标注", font=f_sub, fill=BLUE, anchor="la")
    y += 26 + 22

    for line in ["把一张软件截图，变成看得懂的说明图。",
                 "标注图 PNG + 可交互 HTML，同一份数据驱动。"]:
        d.text((x, y), line, font=f_body, fill=MUTED, anchor="la")
        y += 28

    y += 16
    for item in ["编号圆点自动避让文字，不压字",
                 "悬停编号 ↔ 图例双向定位",
                 "附可复现 demo，克隆即用"]:
        d.ellipse([x + 2, y + 8, x + 8, y + 14], fill=BLUE)
        d.text((x + 20, y), item, font=f_item, fill=MUTED, anchor="la")
        y += 28

    d.text((x, H - 66), "github.com/han719307-dotcom/screenshot-ui-explainer",
           font=f_url, fill=DIM, anchor="la")

    im.save(OUT)
    print(f"{OUT}  {im.size[0]}x{im.size[1]}  {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
