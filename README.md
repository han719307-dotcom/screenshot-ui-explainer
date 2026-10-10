# Screenshot UI Explainer · 界面截图标注

把一个 AI Agent 变成「界面解说员」：丢给它一张软件截图，它还你一张**看得懂的标注图**和一份**可交互的说明页**。

> 遵循开放的 `SKILL.md` 规范，**不绑定特定 Agent** —— WorkBuddy / Claude Code / Codex CLI / Gemini CLI / Cursor / Copilot 等都能用；也可以完全脱离 Agent，当普通 Python 命令行工具跑。

> A skill that turns a raw UI screenshot into an annotated diagram plus a self-contained interactive HTML explainer — with precise dot placement driven by pixel scanning instead of eyeballing.

![demo](examples/output/demo-annotated.png)

<p align="center"><em>示例产物：编号圆点落在界面元素旁，右侧按区域分组给出「这块地方是干什么用的」+ 逐项说明</em></p>

## 它产出什么

| 交付物 | 内容 | 适用场景 |
|---|---|---|
| **标注图 PNG** | 原图叠加编号圆点 + 右侧分组图例面板（含每个区域的功能说明） | 发群里、贴文档、PPT 里用 |
| **交互式 HTML** | 单文件自包含（图片 base64 内嵌），悬停编号 ↔ 图例双向高亮，点击互相滚动定位 | 发链接、让用户自己点着看 |

示例产物就在仓库里，可以直接打开看：

- 标注图：[`examples/output/demo-annotated.png`](examples/output/demo-annotated.png)
- 交互页：[`examples/output/demo-annotated.html`](examples/output/demo-annotated.html)（下载后用浏览器打开）

## 核心理念：先测区域、再量坐标、后交付

大多数"截图标注"做不好的原因只有两个：**区域划分太碎**、**圆点位置靠目测**。这个 skill 强制走三步：

1. **先分区域**——顶栏 / 侧栏 / 主内容 / 底栏。每个区域先写一段 50-90 字的「这块地方是干什么用的」，再逐条列控件。读者先理解结构，再看细节。
2. **坐标必须量**——用 `locate_elements.py` 按行带扫描像素，拿到真实的 x 区间与中心点。目测坐标必然让圆点压住文字。
3. **生成后必须回看**——把 PNG 读回来逐项检查圆点是否压字、图例是否被裁、编号与图例是否对得上。**不交付未经回看的首轮结果。**

## 使用方式

这个 skill **不绑定任何特定的 AI Agent**。它遵循开放的 `SKILL.md` 规范，
并且真正干活的是四个普通 Python 命令行脚本 —— 任何能执行 shell 命令的 Agent 都能用，
不用 Agent 也能用。

### 方式一：装进任意支持 SKILL.md 的 Agent

本仓库**根目录就是 skill 本体**（`SKILL.md` 在根目录），克隆后放进对应目录即可：

```bash
git clone https://github.com/han719307-dotcom/screenshot-ui-explainer.git <目标目录>
```

各 Agent 的 skills 目录（**以你所用版本的官方文档为准**，下表为 2026 年的通用情况）：

| Agent | 用户级（全局） | 项目级 |
|---|---|---|
| **通用约定**（多个 Agent 都认） | — | `.agents/skills/` |
| WorkBuddy | `~/.workbuddy/skills/` | `.workbuddy/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex CLI | `~/.codex/skills/` | `.codex/skills/` |
| Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/` |
| Cursor | —（仅项目级） | `.cursor/skills/` |
| GitHub Copilot | `~/.config/github-copilot/skills/` | `.github/skills/` |

举例：

```bash
# WorkBuddy / Claude Code / Gemini CLI 任选其一
git clone https://github.com/han719307-dotcom/screenshot-ui-explainer.git \
  ~/.workbuddy/skills/screenshot-ui-explainer

# Cursor 只能放项目里
git clone https://github.com/han719307-dotcom/screenshot-ui-explainer.git \
  .cursor/skills/screenshot-ui-explainer
```

> `~` 在 Windows 上指 `C:\Users\<你的用户名>`。
>
> **目录名要和 SKILL.md 里的 `name` 一致**（都是 `screenshot-ui-explainer`），
> 这是规范要求，改错会导致 skill 识别不到。
>
> 如果某个 Agent 不原生支持 `SKILL.md`，就用它的规则文件（如 `AGENTS.md`）写一句
> "需要标注界面截图时，读 `<路径>/SKILL.md` 并按其中步骤执行"，指向同一份文件即可，
> 不要把内容复制成两份。

### 方式二：当独立命令行工具用

不装 skill 也行，只要 Python 3 和 Pillow：

```bash
git clone https://github.com/han719307-dotcom/screenshot-ui-explainer.git
cd screenshot-ui-explainer
python -m venv .venv
.venv/Scripts/pip install pillow      # Windows
# source .venv/bin/activate && pip install pillow   # macOS / Linux
```

## 三步走完流程

```bash
# 1) 量坐标：扫描顶部导航栏、侧栏、输入区，输出 x 区间与真实中心点
#    深色底/浅色底都支持，默认自动判断
python scripts/locate_elements.py shot.png \
  --band "20 62 1700 2544:TOPBAR" \
         "115 180 0 520:SIDEBAR" \
         "350 395 880 2200:COMPOSER"

# 2) 写 annotations.json（格式见 references/annotations-schema.md）

# 3) 一条命令产出两份交付物（只读你的 JSON，不会改写它）
python scripts/build_annotation_demo.py shot.png annotations.json -o output --name 界面标注
```

也可以分开生成：

```bash
python scripts/annotate_png.py  annotations.json -o 标注图.png --theme light
python scripts/annotate_html.py annotations.json -o 界面标注.html --theme light
```

### 脚本一览

| 脚本 | 用途 | 何时用 |
|---|---|---|
| `locate_elements.py` | 按行带扫描亮色元素，输出 x 区间与中心点 | 定位坐标，必用 |
| `annotate_png.py` | 生成带编号 + 图例面板的标注图 PNG | 需要图片交付物时 |
| `annotate_html.py` | 生成自包含可交互标注页面 | 需要网页交付物时 |
| `build_annotation_demo.py` | 一条命令跑通全流程 | 两份都要时，推荐 |

常用参数：

| 参数 | 作用 |
|---|---|
| `--theme dark\|light` | 图例面板与引线配色，默认 `dark` |
| `--panel-width` | 右侧图例带宽，默认 620 |
| `--dot-radius` | 圆点基准半径（原图像素），默认 15；窄区域可调小 |
| `--leader-threshold` | 圆点离元素超过多少像素才画引线，默认 60 |
| `--no-leader` | 完全不画引线 |
| `--font` / `--font-bold` | 指定中文字体文件 |
| `--no-panel` | 只画编号圆点，不拼图例面板 |

## 复现示例

仓库里的 demo 完全可复现，不需要你有现成截图：

```bash
cd examples
python make_demo_shot.py                     # 生成模拟界面截图 demo-dashboard.png
python ../scripts/build_annotation_demo.py demo-dashboard.png annotations.json \
  -o output --name demo-annotated --theme light
```

`examples/annotations.json` 同时也是**格式的最佳参考**：17 条标注覆盖 4 个区域，演示了
分组说明、按区域连续编号、用 `dot_r` 把圆点缩进窄顶栏、以及用 `label_x` 把圆点挪离按钮文字
（距离远了会自动出现引线）。

> 这个文件用 `build_annotation_demo.py` 跑完后**不会被修改**（v1.0.1 起）。
> 早期版本会把原图绝对路径回写进去，现已移除该行为。

## annotations.json 速览

```json
{
  "title": "SaaS 控制台界面标注",
  "subtitle": "示例素材 · 浅色主题",
  "source": "demo-dashboard.png",
  "group_notes": {
    "顶部导航栏": "整个应用的全局控制区，任何页面都在最上方。负责跨页面的搜索、通知与账号操作……"
  },
  "annotations": [
    { "n": 1, "x": 73, "y": 29, "group": "顶部导航栏",
      "title": "品牌徽标（Logo）",
      "desc": "点击回到产品首页。",
      "label_x": 30, "label_y": 29 },

    { "n": 3, "x": 1356, "y": 29, "group": "顶部导航栏",
      "title": "帮助与设置图标",
      "desc": "两个并排的线框图标，宽度都只有 20px 左右。",
      "dot_r": 11 },

    { "n": 16, "x": 1180, "y": 644, "group": "主内容区",
      "title": "创建项目（绿色主按钮）",
      "desc": "卡片右下角的主操作按钮。",
      "label_x": 1000, "label_y": 644 }
  ]
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `n` | ✅ | 编号，全局唯一，**按区域顺序连续编号**图例读起来才顺 |
| `x` / `y` | ✅ | **元素自身的定位点**（一般取元素视觉中心），原图像素坐标，脚本自动换算百分比，**不要手工折算** |
| `group` | ✅ | 分组名，相同值自动归入同一图例分区 |
| `title` | ✅ | 条目标题，建议 `英文原名（中文解释）` |
| `desc` | 可选 | 详细说明，**只在 HTML 中展示** |
| `label_x` / `label_y` | 可选 | **圆点实际画在哪**，用于把圆点挪开避免压字 |
| `dot_r` | 可选 | 该条圆点半径（原图像素），窄区域塞不下时缩小它 |
| `group_notes` | ✅ | 每个分组一段区域功能说明，50-90 字 |

> `x`/`y` 与 `label_x`/`label_y` 分工不同：前者回答"这条标注指的是哪里"，后者回答"圆点画在哪"。
> 两者相距超过 `--leader-threshold`（默认 60px）时，脚本会自动补一条带描边的引线把圆点连回元素。

完整字段说明、坐标换算规则与常见错误见 [`references/annotations-schema.md`](references/annotations-schema.md)；
拆解界面时的部件中英文对照表见 [`references/common-ui-parts.md`](references/common-ui-parts.md)。

## 踩过的坑（已验证的实践结论）

- **图例可以比截图高**——标注 ≥ 11 条时图例自然超过原图高度，正确做法是加高整张画布（脚本已处理），而不是压缩行距或裁掉内容。
- **`label_x` / `label_y` 是最有用的逃生舱**——约 1/4 的标注需要单独微调圆点位置，尤其是绿色实心主按钮、`⋯` 更多菜单、长标题旁的编号。数据里保留 `x`/`y` 为元素定位点，微调只写 `label_x`/`label_y`，后续换图重测时更容易分辨。
- **窄区域优先缩圆点，其次就近挪位，最后才用引线**——顶栏小图标这类元素，`dot_r: 11` 往往一改就解决；引线是补救手段，用多了整张图会显得凌乱。
- **别用目测坐标**——`center_y` 现在回扫区间纵向范围得出真实中心，比"取行带中点"准确得多；但纵向范围只能在 `--band` 内测量，所以行带上下要留余量。
- **扫描不以明暗为前提**——同一张图反色前后，`auto` 模式的扫描结果完全一致。
- **空状态和进度条必须标**——`No repositories found`、`0/3 complete` 这类元素用户往往最想问"这什么意思"，反而最容易被漏掉。
- **HTML 配色跟界面主题走，不要跟截图走**；而截图区域本身保持原样不动。
- **深色截图配深色图例面板**看起来最像"一张图"。

## 已知限制

- 坐标与截图强绑定：截图被缩放或裁剪后必须重新测量，不能沿用旧值。
- `locate_elements.py` 的纵向范围只能在指定的 `--band` 内测量，元素比行带高时 `y` 会被裁到行带边界——**行带上下要留余量**。
- 行带里本来就没有留白的密集区域（例如整行都是紧挨的图标），扫描结果仍可能连成一片，此时需要缩窄行带或手工测量。
- HTML 版把原图以 base64 内嵌，截图很大时文件会偏大（1600×1000 的示例约 100 KB，4K 截图可能到几 MB）。
- 中文渲染依赖系统字体。脚本按 `msyh.ttc → PingFang.ttc → NotoSansCJK → wqy-zenhei` 顺序自动探测，
  全部找不到时回退到 Pillow 内置字体并打印告警，此时中文会显示为方块，需用 `--font` 指定。
- 需要 Pillow；纯标准库环境无法运行。

## 仓库结构

```
screenshot-ui-explainer/
├── SKILL.md                          # skill 定义（Agent 读取的入口）
├── CHANGELOG.md                      # 版本变更记录
├── scripts/
│   ├── locate_elements.py            # 像素扫描定位（深底/浅底自动判断）
│   ├── annotate_png.py              # 标注图 PNG 生成
│   ├── annotate_html.py             # 交互式 HTML 生成
│   └── build_annotation_demo.py     # 一键跑通全流程（只读输入 JSON）
├── references/
│   ├── annotations-schema.md        # annotations.json 完整字段说明
│   └── common-ui-parts.md           # 常见界面部件中英对照速查
├── docs/
│   ├── make_social_preview.py       # 生成 GitHub 社交预览图
│   └── social-preview.png           # 1280×640 社交预览图
└── examples/
    ├── make_demo_shot.py            # 生成模拟截图（可复现 demo）
    ├── demo-dashboard.png           # 模拟界面截图
    ├── annotations.json             # 示例标注数据（17 条 / 4 组）
    └── output/                      # 示例产物
```

## 版本

当前 v1.0.1，变更见 [CHANGELOG.md](CHANGELOG.md)。

## License

[MIT](LICENSE)
