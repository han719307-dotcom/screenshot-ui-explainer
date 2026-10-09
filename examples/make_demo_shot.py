#!/usr/bin/env python3
"""
make_demo_shot.py - 生成一张模拟的 SaaS 控制台截图，作为本 skill 的示例素材。

这不是 skill 的正式流程的一部分，只是为了让仓库里的 demo 可复现：
运行后得到 examples/demo-dashboard.png，再用 examples/annotations.json 走一遍
annotate_png.py / annotate_html.py，就能复现 README 里的效果图。

用法：
    python examples/make_demo_shot.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1000

INK = (31, 35, 40)          # 主文字
GREY = (107, 114, 128)      # 次要文字
LINE = (228, 231, 236)      # 分隔线
PANEL = (247, 248, 250)     # 顶栏 / 侧栏底色
ACCENT = (11, 87, 208)      # 主题蓝
GREEN = (31, 136, 61)       # 主操作按钮
CHIP = (241, 243, 246)      # 胶囊按钮底色

HERE = Path(__file__).resolve().parent
OUT = HERE / "demo-dashboard.png"

FONT_DIR = Path(r"C:\Windows\Fonts")
FONTS = {
    "regular": ["msyh.ttc", "PingFang.ttc", "NotoSansCJK-Regular.ttc"],
    "bold": ["msyhbd.ttc", "PingFang.ttc", "NotoSansCJK-Bold.ttc"],
}


def load(kind, size):
    for name in FONTS[kind]:
        p = FONT_DIR / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    for p in ("/System/Library/Fonts/PingFang.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    raise SystemExit("未找到中文字体，请自行安装 msyh / PingFang / Noto Sans CJK")


def rounded(d, box, radius, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(d, cx, cy, text, font, fill):
    bb = d.textbbox((0, 0), text, font=font)
    d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]),
           text, font=font, fill=fill)


def main():
    f_h1 = load("bold", 30)
    f_h2 = load("bold", 20)
    f_h3 = load("bold", 16)
    f_body = load("regular", 15)
    f_small = load("regular", 13)
    f_tiny = load("regular", 12)

    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    # ---------------- 顶部导航栏 ----------------
    d.rectangle([0, 0, W, 56], fill=PANEL)
    d.line([0, 56, W, 56], fill=LINE)
    rounded(d, [60, 16, 86, 42], 7, fill=ACCENT)
    center_text(d, 73, 29, "C", f_h3, (255, 255, 255))

    rounded(d, [112, 14, 492, 42], 8, fill=(238, 240, 243))
    d.text((132, 21), "搜索项目、文档、成员…", font=f_small, fill=GREY)
    d.text((448, 21), "/", font=f_small, fill=(160, 166, 176))

    for cx in (1330, 1382):
        d.ellipse([cx - 9, 20, cx + 9, 38], outline=GREY, width=2)
    center_text(d, 1382, 29, "?", f_tiny, GREY)
    d.ellipse([1434, 21, 1448, 35], outline=GREY, width=2)
    d.ellipse([1450, 29, 1470, 49], fill=(124, 58, 237))
    center_text(d, 1460, 39, "A", f_tiny, (255, 255, 255))

    # ---------------- 左侧边栏 ----------------
    d.rectangle([0, 57, 250, H], fill=PANEL)
    d.line([250, 57, 250, H], fill=LINE)
    d.text((24, 82), "我 的 工 作 台", font=f_tiny, fill=(150, 156, 166))

    nav = ["首页", "动态流", "探索"]
    for i, label in enumerate(nav):
        y = 112 + i * 44
        rounded(d, [24, y + 3, 42, y + 21], 5, fill=(222, 226, 232))
        d.text((58, y), label, font=f_body, fill=INK)

    # 当前选中项：高亮底 + 左侧蓝色指示条
    rounded(d, [12, 240, 238, 284], 8, fill=(232, 238, 251))
    d.rectangle([12, 240, 16, 284], fill=ACCENT)
    rounded(d, [24, 251, 42, 269], 5, fill=ACCENT)
    d.text((58, 248), "项目", font=f_body, fill=ACCENT)

    d.line([16, 308, 234, 308], fill=LINE)
    d.text((24, 324), "我的仓库", font=f_tiny, fill=(150, 156, 166))

    # 空状态区块
    rounded(d, [16, 348, 234, 448], 10, fill=(255, 255, 255), outline=LINE, width=2)
    center_text(d, 125, 380, "暂无仓库", f_body, INK)
    center_text(d, 125, 402, "No repositories found", f_tiny, GREY)
    rounded(d, [72, 414, 178, 442], 7, fill=ACCENT)
    center_text(d, 125, 428, "新建仓库", f_small, (255, 255, 255))

    d.text((24, 468), "已用 2 / 10 个项目", font=f_tiny, fill=GREY)

    # ---------------- 主内容区 ----------------
    d.text((290, 96), "下午好，Alex", font=f_h1, fill=INK)
    d.text((290, 140), "你还有 3 项入门任务未完成", font=f_body, fill=GREY)

    # 输入区
    rounded(d, [290, 184, 1330, 320], 14, fill=(255, 255, 255), outline=(208, 213, 221), width=2)
    d.text((316, 212), "描述你想让 AI 做的事，输入 @ 引用项目文件…", font=f_body, fill=(150, 156, 166))

    for i, (label, w, on) in enumerate([("Ask", 54, False), ("Agent", 70, True), ("Plan", 58, False)]):
        x = 316 + [0, 64, 144][i]
        rounded(d, [x, 268, x + w, 300], 16,
                fill=ACCENT if on else CHIP)
        center_text(d, x + w / 2, 284, label, f_small,
                    (255, 255, 255) if on else GREY)

    d.ellipse([1258, 252, 1298, 292], fill=ACCENT)
    d.polygon([(1272, 282), (1284, 262), (1290, 276), (1281, 276)], fill=(255, 255, 255))

    # 快捷操作胶囊
    x = 290
    for label, w in [("调试代码", 96), ("写单元测试", 112), ("创建 Issue", 104), ("生成文档", 96)]:
        rounded(d, [x, 344, x + w, 380], 18, fill=CHIP)
        center_text(d, x + w / 2, 362, label, f_small, GREY)
        x += w + 14

    # 入门清单卡片
    rounded(d, [290, 412, 1330, 700], 14, fill=(251, 252, 253), outline=LINE, width=2)
    d.text((316, 438), "入门清单", font=f_h2, fill=INK)
    d.text((1196, 446), "0/3 complete", font=f_small, fill=GREY)
    rounded(d, [316, 480, 1304, 490], 5, fill=(232, 235, 240))

    for i, item in enumerate(["连接你的第一个仓库", "邀请一位协作者", "创建第一个项目"]):
        y = 518 + i * 48
        rounded(d, [316, y, 338, y + 22], 5, fill=(255, 255, 255), outline=(200, 206, 214), width=2)
        d.text((352, y + 1), item, font=f_body, fill=INK)

    rounded(d, [1080, 620, 1280, 668], 10, fill=GREEN)
    center_text(d, 1180, 644, "创建项目", f_h3, (255, 255, 255))

    # 右侧推荐卡片
    rounded(d, [1354, 412, 1576, 588], 14, fill=(251, 252, 253), outline=LINE, width=2)
    d.text((1376, 436), "推荐内容", font=f_h3, fill=INK)
    d.text((1538, 434), "×", font=f_h2, fill=GREY)
    for i, t in enumerate(["界面标注最佳实践", "如何写出好用的 Skill", "新手引导设计清单"]):
        y = 478 + i * 32
        d.ellipse([1378, y + 6, 1386, y + 14], fill=ACCENT)
        d.text((1398, y), t, font=f_small, fill=GREY)

    im.save(OUT)
    print(f"{OUT}  {im.size}")


if __name__ == "__main__":
    main()
