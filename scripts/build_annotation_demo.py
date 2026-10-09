#!/usr/bin/env python3
"""
build_annotation_demo.py - 一条命令跑通"截图 -> 标注图 PNG + 可交互 HTML"全流程。

把 locate_elements.py 的扫描结果当起点，用一份 annotations.json 同时产出两种交付物。
既可作为 skill 的自检示例，也可直接改造成具体任务的入口脚本。

用法：
    python build_annotation_demo.py <screenshot.png> annotations.json -o <output_dir>
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
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="截图路径")
    ap.add_argument("annotations", help="annotations.json 路径")
    ap.add_argument("-o", "--outdir", default="output")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--name", default="界面标注")
    args = ap.parse_args()

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    # 统一把 source / title 写进 JSON，后面两个脚本就不用重复传图。
    # 注意：顶层既可能是 {"annotations": [...]}，也可能直接是 [...]（数组形态），
    # 两种都要支持——只处理字典会让数组形态丢失 source，后续脚本直接报错退出。
    src = Path(args.annotations)
    data = json.loads(src.read_text(encoding="utf-8"))
    img_abs = str(Path(args.image).resolve())
    if isinstance(data, dict):
        data["source"] = img_abs
        data.setdefault("title", args.name)
    else:
        data = {"title": args.name, "source": img_abs, "annotations": data}
    src.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    py = sys.executable
    png = out / f"{args.name}.png"
    html = out / f"{args.name}.html"

    run([py, HERE / "annotate_png.py", src, "-o", png, "--theme", args.theme])
    run([py, HERE / "annotate_html.py", src, "-o", html, "--theme", args.theme])

    print("\n完成：")
    print(" -", png)
    print(" -", html)


if __name__ == "__main__":
    main()
