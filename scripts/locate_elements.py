#!/usr/bin/env python3
"""
locate_elements.py - 在截图的行带里扫描元素，输出横向区间与**真实垂直中心**，
把"文字/按钮/图标"的精确定位从"靠猜"变成"靠数据"。

深色与浅色界面都支持，默认自动判断：

  auto      （默认）以行带内像素的**中位灰度**作为背景估计，
            某列只要有像素与背景的亮度差超过 --delta，就算"该列有内容"。
            暗底亮字、亮底暗字、浅色底上的彩色实心按钮都能扫出来。
  dark-bg   老式"暗底找亮元素"：某列最大灰度 > --threshold 即有内容。
  light-bg  亮底找暗元素：某列最小灰度 < --threshold 即有内容。

用法：
    python locate_elements.py shot.png --band "20 62 1700 2544:TOPBAR"
    python locate_elements.py shot.png --band "20 62 0 1600:TOPBAR" "115 180 0 520:SIDEBAR"
    python locate_elements.py shot.png --band "20 62 0 1600:TOPBAR" --mode light-bg --threshold 200
    python locate_elements.py shot.png --band "20 62 0 1600:TOPBAR" --json

输出：每个区间的横向范围 + 真实垂直范围，center_x / center_y 可直接当 x / y 用。

    TOPBAR  y=20-62  x=0-1600  [auto] 背景灰度≈18  delta=40
        [34, 56]   width=23   center_x=45   center_y=29   (纵向 18-40)

原理：对 band 内每一列判断"是否有内容"（见上方三种模式），把连续列合并成区间
（可跨过 merge-gap 像素的小空洞，避免一个字被切成好几段），再对每个区间回扫纵向范围，
取真实上下边界求中心——比直接取行带中点准确得多。标注点一般落在元素内部空白处或正上方。
"""

import argparse
import json
import sys


def load_gray(path):
    try:
        from PIL import Image
    except ImportError:
        sys.exit("需要 Pillow：pip install pillow")
    return Image.open(path).convert("L")


def band_background(im, y0, y1, x0, x1):
    """用行带内像素的中位灰度作为背景估计。

    中位数对"少量前景像素"稳健：UI 截图里背景通常占大多数，
    即使文字、按钮占掉三四成，中位数仍然落在背景色上。
    """
    hist = im.crop((x0, y0, x1, y1)).histogram()
    half = sum(hist) / 2
    acc = 0
    for v, c in enumerate(hist):
        acc += c
        if acc >= half:
            return v
    return 128


def build_grid(px, y0, y1, x0, x1, mode, param, bg):
    """把行带区域转成布尔网格 grid[dy][dx]：该像素是否算"内容"。"""
    grid = []
    for y in range(y0, y1):
        row = []
        for x in range(x0, x1):
            v = px[x, y]
            if mode == "dark-bg":
                on = v > param
            elif mode == "light-bg":
                on = v < param
            else:  # auto：与背景的亮度差
                on = abs(v - bg) > param
            row.append(on)
        grid.append(row)
    return grid


def runs_in_grid(grid, x0, y0, merge_gap):
    """按列合并成横向区间，再回扫每个区间的纵向范围。

    返回 [{"x0","x1","y0","y1","width","center_x","center_y"}, ...]（均为原图绝对坐标）
    """
    cols = len(grid[0]) if grid else 0
    flags = [any(grid[dy][dx] for dy in range(len(grid))) for dx in range(cols)]

    raw, start = [], None
    for i, on in enumerate(flags):
        if on and start is None:
            start = i
        elif not on and start is not None:
            raw.append([start, i - 1])
            start = None
    if start is not None:
        raw.append([start, cols - 1])

    merged = []
    for r in raw:
        if merged and r[0] - merged[-1][1] <= merge_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)

    out = []
    for s, e in merged:
        ys = [dy for dy in range(len(grid)) if any(grid[dy][s:e + 1])]
        if not ys:
            continue
        ax0, ax1 = x0 + s, x0 + e
        ay0, ay1 = y0 + ys[0], y0 + ys[-1]
        out.append({
            "x0": ax0, "x1": ax1, "y0": ay0, "y1": ay1,
            "width": ax1 - ax0 + 1,
            "center_x": (ax0 + ax1) // 2,
            "center_y": (ay0 + ay1) // 2,
        })
    return out


def main():
    ap = argparse.ArgumentParser(description="扫描截图中的元素区间与中心点")
    ap.add_argument("image", help="截图路径")
    ap.add_argument("--band", nargs="+", required=True,
                    help="每组 4 个数字：y0 y1 x0 x1；可写 'y0 y1 x0 x1:名称'，多组重复传参")
    ap.add_argument("--label", nargs="*", default=None, help="与 band 一一对应的名称")
    ap.add_argument("--mode", choices=["auto", "dark-bg", "light-bg"], default="auto",
                    help="auto（默认，自动判断深浅底）/ dark-bg（暗底找亮）/ light-bg（亮底找暗）")
    ap.add_argument("--delta", type=int, default=40,
                    help="auto 模式下与背景亮度差多少算有内容，默认 40")
    ap.add_argument("--threshold", type=int, default=70,
                    help="dark-bg / light-bg 模式的绝对灰度阈值，默认 70")
    ap.add_argument("--merge-gap", type=int, default=12, help="合并间隔像素，默认 12")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    bands, inline_labels = [], []
    for item in args.band:
        for chunk in item.split(","):
            if ":" in chunk:
                chunk, nm = chunk.split(":", 1)
            else:
                nm = None
            nums = [int(v) for v in chunk.replace("=", " ").split()]
            if len(nums) != 4:
                sys.exit(f"band 需要 4 个数字 (y0 y1 x0 x1)，收到: {chunk!r}")
            bands.append(nums)
            inline_labels.append(nm)

    im = load_gray(args.image)
    px = im.load()
    W, H = im.size

    labels, auto = [], 0
    for nm in inline_labels:
        auto += 1
        labels.append(nm or f"band{auto}")
    labels = args.label or labels

    param = args.delta if args.mode == "auto" else args.threshold
    out = {}
    for name, (y0, y1, x0, x1) in zip(labels, bands):
        # 越界裁剪，避免局部反查时坐标失真
        y0, y1 = max(0, y0), min(H, y1)
        x0, x1 = max(0, x0), min(W, x1)
        if y1 <= y0 or x1 <= x0:
            sys.exit(f"{name}: 行带范围无效 y={y0}-{y1} x={x0}-{x1}（图片尺寸 {W}x{H}）")

        bg = band_background(im, y0, y1, x0, x1)
        mode = args.mode
        if mode == "auto":
            # 背景偏暗 → 元素通常更亮；背景偏亮 → 元素通常更暗。
            # 这里只用于打印提示，判定本身用的是"与背景的亮度差"，与明暗无关。
            hint = "暗底" if bg < 128 else "亮底"
            header = f"[auto] 背景灰度≈{bg}（{hint}） delta={param}"
        else:
            header = f"[{mode}] threshold={param} 背景灰度≈{bg}"

        grid = build_grid(px, y0, y1, x0, x1, mode, param, bg)
        res = runs_in_grid(grid, x0, y0, args.merge_gap)
        out[name] = res

        print(f"{name}  y={y0}-{y1}  x={x0}-{x1}  {header}")
        if not res:
            print("    （未发现内容：可调低 --delta，或改用 --mode light-bg / dark-bg 并调 --threshold）")
        for r in res:
            print(f"    [{r['x0']}, {r['x1']}]   width={r['width']}   "
                  f"center_x={r['center_x']}   center_y={r['center_y']}   "
                  f"(纵向 {r['y0']}-{r['y1']})")
        print()

    print(f"图片尺寸: {W} x {H}")

    if args.json:
        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
