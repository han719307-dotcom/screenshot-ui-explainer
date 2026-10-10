#!/usr/bin/env python3
"""
build_annotation_demo.py - 一条命令跑通"截图 -> 标注图 PNG + 可交互 HTML"全流程。

一份 annotations.json 同时驱动两种交付物。既可作为 skill 的自检示例，
也可直接改造成具体任务的入口脚本。

用法：
    python build_annotation_demo.py <screenshot.png> annotations.json -o <output_dir>

关于输入文件：**本脚本只读不写**。原图路径、标题、副标题都通过命令行参数传给下游脚本，
不会修改你的 annotations.json（v1.0.1 之前会把 source 绝对路径回写进去，现已移除该行为）。
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(cmd):
    print("$", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def main():
    ap = argparse.ArgumentParser(description="一键产出标注图 PNG + 交互式 HTML")
    ap.add_argument("image", help="截图路径")
    ap.add_argument("annotations", help="annotations.json 路径（只读，不会被修改）")
    ap.add_argument("-o", "--outdir", default="output")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--name", default="界面标注", help="输出文件名（不含扩展名）")
    ap.add_argument("--title", default=None, help="标题，默认取 JSON 里的 title，再退回 --name")
    ap.add_argument("--subtitle", default=None, help="副标题，默认取 JSON 里的 subtitle")
    ap.add_argument("--dot-radius", type=int, default=15, help="圆点基准半径，默认 15")
    ap.add_argument("--no-leader", action="store_true", help="圆点被挪开时不画引线")
    ap.add_argument("--leader-threshold", type=int, default=60,
                    help="圆点离元素超过这个像素距离才画引线，默认 60")
    args = ap.parse_args()

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    src = Path(args.annotations)
    if not src.exists():
        sys.exit(f"找不到标注文件：{src}")
    data = json.loads(src.read_text(encoding="utf-8"))

    # 顶层既可能是 {"annotations": [...]}，也可能直接是 [...]（数组形态），两种都要支持。
    items = data["annotations"] if isinstance(data, dict) else data
    if not items:
        sys.exit(f"{src} 里没有标注条目")

    img = Path(args.image)
    if not img.exists():
        sys.exit(f"找不到截图：{img}")

    title = (args.title
             or (data.get("title") if isinstance(data, dict) else None)
             or args.name)
    subtitle = args.subtitle or (data.get("subtitle") if isinstance(data, dict) else None)

    common = ["-i", str(img.resolve()), "--theme", args.theme, "--title", title]
    if subtitle:
        common += ["--subtitle", subtitle]
    if args.no_leader:
        common += ["--no-leader"]
    if args.dot_radius != 15:
        common += ["--dot-radius", str(args.dot_radius)]
    if args.leader_threshold != 60:
        common += ["--leader-threshold", str(args.leader_threshold)]

    py = sys.executable
    png = out / f"{args.name}.png"
    html = out / f"{args.name}.html"

    run([py, HERE / "annotate_png.py", src] + common + ["-o", png])
    run([py, HERE / "annotate_html.py", src] + common + ["-o", html])

    print(f"\n完成（共 {len(items)} 条标注）：")
    print(" -", png)
    print(" -", html)
    print(f"\n提示：{src} 未被修改。")


if __name__ == "__main__":
    main()
