#!/usr/bin/env python3
"""
annotate_html.py - 生成自包含的可交互标注页面：
左侧原图叠加编号圆点，右侧分组图例；悬停编号/条目双向高亮，点击互相滚动定位。
图片以 base64 内嵌，单文件即可分享，无外部依赖。

用法：
    python annotate_html.py annotations.json -o 界面标注.html [--theme dark|light]

annotations.json 格式见 annotate_png.py 的说明。
顶层可选字段：title / subtitle / source。
"""

import argparse
import base64
import json
import math
import sys
from pathlib import Path

TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 28px 24px 56px;
    background: {page_bg}; color: {fg};
    font-family: "Microsoft YaHei", "PingFang SC", system-ui, -apple-system, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 1180px; margin: 0 auto; }}
  header h1 {{ font-size: 22px; margin: 0 0 6px; letter-spacing: .2px; }}
  header p {{ margin: 0; color: {grey}; font-size: 13px; line-height: 1.7; }}
  .tip {{ display:inline-block; margin-top:10px; padding:5px 10px; border-radius:999px;
          background:{tip_bg}; color:{accent}; font-size:12px; }}
  .stage {{
    position: relative; margin: 20px 0 34px; border-radius: 14px; overflow: hidden;
    background: {stage_bg}; border: 1px solid {border};
    box-shadow: 0 10px 30px rgba(16,24,40,.12);
  }}
  .stage img {{ display: block; width: 100%; height: auto; }}
  .badge {{
    position: absolute; transform: translate(-50%,-50%);
    width: 26px; height: 26px; border-radius: 50%;
    background: #f04438; color: #fff; border: 2px solid rgba(255,255,255,.92);
    font-size: 12.5px; font-weight: 700; line-height: 22px; text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,.45); cursor: pointer;
    transition: transform .15s ease, background .15s ease;
    user-select: none;
  }}
  .badge:hover, .badge.active {{ transform: translate(-50%,-50%) scale(1.35); background:{accent}; z-index: 5; }}
  .leaders {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }}
  .leaders line, .leaders circle {{ vector-effect: non-scaling-stroke; stroke-linecap: round; }}
  .leaders .halo {{ stroke: {lead_halo}; stroke-width: 4.5; fill: none; }}
  .leaders .mark {{ stroke: {lead}; stroke-width: 2; fill: none; }}
  .legend {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 16px; }}
  .group {{ background:{card_bg}; border:1px solid {border}; border-radius:12px; padding:14px 16px 8px; }}
  .group h3 {{
    margin:0 0 10px; font-size:13px; color:{accent}; letter-spacing:.4px;
    padding-bottom:8px; border-bottom:1px dashed {border};
  }}
  .group .note {{
    margin: 0 0 10px; padding: 8px 10px; border-radius: 7px;
    background: {note_bg}; border-left: 3px solid {accent};
    font-size: 12.5px; color: {grey}; line-height: 1.7;
  }}
  .group .note b {{ color: {fg}; font-weight: 600; }}
  .list {{ list-style:none; margin:0; padding:0; }}
  .item {{ display:flex; gap:10px; padding:7px 6px; border-radius:8px; transition:background .15s; }}
  .item:hover, .item.active {{ background:{hover}; }}
  .chip {{
    flex: 0 0 22px; width:22px; height:22px; border-radius:50%; background:#f04438; color:#fff;
    font-size:12px; font-weight:700; text-align:center; line-height:22px; margin-top:1px;
  }}
  .item.active .chip, .item:hover .chip {{ background:{accent}; }}
  .txt b {{ font-size:13.5px; color:{fg}; }}
  .txt p {{ margin:3px 0 0; font-size:12.5px; color:{grey}; line-height:1.65; }}
  @media (max-width: 860px) {{
    .legend {{ grid-template-columns: 1fr; }}
    .badge {{ width:20px;height:20px;line-height:16px;font-size:11px; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{title}</h1>
    <p>截图共标注 {count} 处。鼠标移到图片上的编号圆点或下方条目，会高亮对应关系，点击可互相定位。</p>
    {subtitle_html}
  </header>

  <div class="stage" id="stage">
    <img src="data:image/png;base64,{img_b64}" alt="{title}">
    {leaders_svg}
    {badges}
  </div>

  <div class="legend" id="legend">
    {groups}
  </div>
</div>

<script>
  const badges = [...document.querySelectorAll('.badge')];
  const items  = [...document.querySelectorAll('.item')];
  function highlight(n, on) {{
    [...badges, ...items].forEach(el => {{
      if (el.dataset.n === n) el.classList.toggle('active', on);
    }});
  }}
  [...badges, ...items].forEach(el => {{
    el.addEventListener('mouseenter', () => highlight(el.dataset.n, true));
    el.addEventListener('mouseleave', () => highlight(el.dataset.n, false));
    el.addEventListener('click', () => {{
      const t = el.classList.contains('badge')
        ? items.find(i => i.dataset.n === el.dataset.n)
        : badges.find(b => b.dataset.n === el.dataset.n);
      if (t) t.scrollIntoView({{behavior:'smooth', block:'center'}});
    }});
  }});
</script>
</body>
</html>
"""

THEMES = {
    "dark": dict(page_bg="#0d1117", fg="#e6edf3", grey="#8b949e", accent="#58a6ff",
                 stage_bg="#0d1117", card_bg="#161b22", border="#30363d",
                 hover="rgba(88,166,255,.12)", tip_bg="rgba(88,166,255,.14)",
                 note_bg="rgba(88,166,255,.08)",
                 lead="#aab2bc", lead_halo="rgba(13,17,23,.95)"),
    "light": dict(page_bg="#f4f5f7", fg="#1f2328", grey="#59636e", accent="#0b57d0",
                  stage_bg="#0d1117", card_bg="#ffffff", border="#e4e7ec",
                  hover="#f3f6fc", tip_bg="#e8eefb", note_bg="#f0f4fd",
                  lead="#6e7681", lead_halo="rgba(255,255,255,.95)"),
}


def collect_group_notes(data):
    """从顶层 group_notes / groups 里取出每个分组的用途说明。"""
    notes = {}
    if isinstance(data, dict):
        for k, v in (data.get("group_notes") or {}).items():
            notes[k] = v
        for g in (data.get("groups") or []):
            if isinstance(g, dict) and g.get("name"):
                notes[g["name"]] = g.get("note", notes.get(g["name"]))
    return notes


def main():
    ap = argparse.ArgumentParser(description="生成可交互标注 HTML")
    ap.add_argument("annotations", help="annotations.json 路径")
    ap.add_argument("-i", "--image", default=None, help="原图路径")
    ap.add_argument("-o", "--output", default="annotated.html")
    ap.add_argument("--theme", choices=["dark", "light"], default="dark")
    ap.add_argument("--title", default=None)
    ap.add_argument("--subtitle", default=None)
    ap.add_argument("--dot-radius", type=int, default=15,
                    help="编号圆点基准半径（原图像素），默认 15；单条可用 dot_r 覆盖")
    ap.add_argument("--no-leader", action="store_true", help="圆点被挪开时不画引线")
    ap.add_argument("--leader-threshold", type=int, default=60,
                    help="圆点离元素超过这个像素距离才画引线，默认 60")
    args = ap.parse_args()

    src = Path(args.annotations)
    data = json.loads(src.read_text(encoding="utf-8"))
    items = data["annotations"] if isinstance(data, dict) else data
    image_path = args.image or (data.get("source") if isinstance(data, dict) else None)
    if not image_path:
        sys.exit("请用 -i 指定原图路径，或在 JSON 顶层提供 source 字段")

    from PIL import Image
    W, H = Image.open(image_path).size
    img_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()

    # 圆点：默认画在 label 位置（没写 label 就等于 x/y），大小可用 dot_r 逐条缩放。
    # 网页里的 26px 对应原图 r=15，因此这里按 r 等比换算，保证小圆点在页面上也小。
    badges, leaders = [], []
    for a in items:
        lx, ly = a.get("label_x", a["x"]), a.get("label_y", a["y"])
        size = max(14, int(round(int(a.get("dot_r") or args.dot_radius) * 26 / 15)))
        badges.append(
            f'<span class="badge" data-n="{a["n"]}" '
            f'style="left:{lx / W * 100:.3f}%;top:{ly / H * 100:.3f}%;'
            f'width:{size}px;height:{size}px;line-height:{size - 4}px;'
            f'font-size:{max(9, round(size * 0.48))}px">{a["n"]}</span>')
        # 圆点被挪得较远时，补一条引线指回元素真实中心 x/y
        if not args.no_leader and math.hypot(a["x"] - lx, a["y"] - ly) > args.leader_threshold:
            leaders.append((lx, ly, a["x"], a["y"]))

    leaders_svg = ""
    if leaders:
        halo, mark = [], []
        for lx, ly, ax, ay in leaders:
            seg = (f'x1="{lx:.1f}" y1="{ly:.1f}" x2="{ax:.1f}" y2="{ay:.1f}"',)
            halo.append(f'<line {seg[0]} class="halo"/>')
            mark.append(f'<line {seg[0]} class="mark"/>')
            halo.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="5" class="halo"/>')
            mark.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="5" class="mark"/>')
        leaders_svg = ('<svg class="leaders" viewBox="0 0 {w} {h}" '
                       'preserveAspectRatio="none" aria-hidden="true">{a}{b}</svg>'
                       ).format(w=W, h=H, a="".join(halo), b="".join(mark))

    order, grouped = [], {}
    for a in items:
        g = a.get("group", "其他")
        if g not in grouped:
            grouped[g] = []
            order.append(g)
        grouped[g].append(a)

    notes = collect_group_notes(data)
    blocks = []
    for g in order:
        lis = "\n".join(
            f'''<li class="item" data-n="{a['n']}">
                  <span class="chip">{a['n']}</span>
                  <div class="txt"><b>{a['title']}</b><p>{a.get('desc','')}</p></div>
                </li>''' for a in grouped[g])
        note_html = (f'<p class="note"><b>这块地方是干什么用的：</b>{notes[g]}</p>'
                     if notes.get(g) else "")
        blocks.append(
            f'<section class="group"><h3>{g}</h3>{note_html}<ul class="list">{lis}</ul></section>')

    title = args.title or (data.get("title") if isinstance(data, dict) else None) or "界面标注"
    sub = args.subtitle or (data.get("subtitle") if isinstance(data, dict) else None)
    html = TPL.format(
        title=title, count=len(items), img_b64=img_b64,
        badges="\n    ".join(badges), groups="\n    ".join(blocks),
        leaders_svg=leaders_svg,
        subtitle_html=f'<span class="tip">{sub}</span>' if sub else "",
        **THEMES[args.theme])

    Path(args.output).write_text(html, encoding="utf-8")
    print(f"{args.output}  {len(html)} bytes")


if __name__ == "__main__":
    main()
