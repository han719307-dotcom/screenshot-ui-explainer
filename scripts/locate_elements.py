#!/usr/bin/env python3
"""
locate_elements.py - 在截图里按行带扫描亮色元素的横向像素区间，
用来把"文字/按钮/图标"的精确定位从"靠猜"变成"靠数据"。

用法：
    python locate_elements.py <image.png> --band 20 62 1700 2544 --label TOPBAR
    python locate_elements.py <image.png> --band 350 395 880 2200,440 480 890 2130

输出：每组 band 的 x 区间列表（原图像素坐标），可直接换算成标注点。

原理：对 band 内每一列取纵向最大灰度值，超过阈值即视为"该列有内容"，
再把连续列合并为区间（可跨过 gap 像素的小空洞，避免一个字被切成好几段）。
标注点一般取区间中心；按钮/图标建议落在元素内部空白处或正上方。
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


def runs_in_band(px, y0, y1, x0, x1, threshold, merge_gap):
    """返回 [[start_x, end_x], ...]，已按 merge_gap 合并相邻区间。"""
    flags = []
    for x in range(x0, x1):
        m = max(px[x, y] for y in range(y0, y1))
        flags.append(m > threshold)

    raw = []
    start = None
    for i, on in enumerate(flags):
        if on and start is None:
            start = i
        elif not on and start is not None:
            raw.append([x0 + start, x0 + i - 1])
            start = None
    if start is not None:
        raw.append([x0 + start, x1 - 1])

    merged = []
    for r in raw:
        if merged and r[0] - merged[-1][1] <= merge_gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return merged


def main():
    ap = argparse.ArgumentParser(description="扫描截图中的元素横向区间")
    ap.add_argument("image", help="截图路径")
    ap.add_argument("--band", nargs="+", required=True,
                    help="每组 4 个数字：y0 y1 x0 x1；可写 'y0 y1 x0 x1:名称'，多组重复传参")
    ap.add_argument("--label", nargs="*", default=None, help="与 band 一一对应的名称")
    ap.add_argument("--threshold", type=int, default=70, help="灰度阈值，默认 70")
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
    labels, auto = [], 0
    for nm in inline_labels:
        auto += 1
        labels.append(nm or f"band{auto}")

    labels = args.label or labels
    out = {}
    for name, (y0, y1, x0, x1) in zip(labels, bands):
        res = runs_in_band(px, y0, y1, x0, x1, args.threshold, args.merge_gap)
        out[name] = res
        print(f"{name}  y={y0}-{y1}  x={x0}-{x1}")
        for s, e in res:
            print(f"    [{s}, {e}]   width={e - s + 1}   center_x={(s + e) // 2} "
                  f"center_y={(y0 + y1) // 2}")
    print(f"\n图片尺寸: {im.size[0]} x {im.size[1]}")

    if args.json:
        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
