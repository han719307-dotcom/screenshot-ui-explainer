# 变更记录

本文件记录本项目所有值得注意的变更，格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.1] - 2026-10-10

### 修复

- **`locate_elements.py` 现在支持浅色界面截图**。原实现按行取列灰度最大值再比阈值，本质是
  "暗底找亮元素"，浅色截图整行都超阈值、扫描结果连成一片。新增 `--mode auto|dark-bg|light-bg`，
  默认 `auto` 以行带内像素的中位灰度估计背景，按"与背景的亮度差"判定内容，与界面明暗无关
  （同一张图反色前后扫描结果一致）。`--delta` 控制灵敏度。
- **`center_y` 现在是被扫描元素的真实垂直中心**，不再返回行带中点。实现方式是对每个横向区间
  回扫纵向范围后取上下边界中点。注意纵向范围受 `--band` 限制，行带上下需留余量。
- **`build_annotation_demo.py` 不再改写传入的 `annotations.json`**。原实现会把原图绝对路径写回
  输入文件（`source` 字段），既意外又会把本机路径泄漏进公开仓库。现在改为只读输入，
  原图路径、标题、副标题全部通过命令行参数传给下游脚本。
- **统一了 `x`/`y` 的文档定义**。此前 `references/annotations-schema.md` 称其为"圆点圆心"，
  而 `SKILL.md` 称其为"元素真实中心"，两处矛盾。现统一为：`x`/`y` 是**元素自身的定位点**，
  `label_x`/`label_y` 是**圆点实际绘制位置**。

### 新增

- **圆点可缩放**：`--dot-radius`（全局，默认 15）与逐条 `"dot_r"`。编号字号随圆点自动缩放。
  用于顶栏等窄区域放不下默认圆点的场景。
- **引线（leader line）**：当 `label_x`/`label_y` 与 `x`/`y` 相距超过 `--leader-threshold`
  （默认 60px）时，自动画一条带描边的引线并在元素处画锚点圆环。PNG 与 HTML 同步支持。
  小幅度微调（< 60px）不画线，避免图面变乱。可用 `--no-leader` 完全关闭。
- **跨 Agent 使用**：SKILL.md 去除了对特定平台字段与工具的硬依赖，README 增加各 Agent
  skills 目录对照表（WorkBuddy / Claude Code / Codex CLI / Gemini CLI / Cursor / Copilot
  以及通用的 `.agents/skills/`）。脚本本身是普通 Python 命令行程序，可完全脱离 Agent 使用。
- `annotate_png.py` / `annotate_html.py` / `build_annotation_demo.py` 新增
  `--title` / `--subtitle` / `--dot-radius` / `--leader-threshold` / `--no-leader` 参数。
- `CHANGELOG.md`。

### 变更（可能影响既有用法）

- `locate_elements.py` 的 `--threshold` 语义收窄：现在只在 `--mode dark-bg|light-bg` 时生效；
  `auto` 模式改用 `--delta`。
- `locate_elements.py --json` 的输出结构由 `{名称: [[x0, x1], ...]}` 变为
  `{名称: [{x0, x1, y0, y1, width, center_x, center_y}, ...]}`，字段更完整。
- `locate_elements.py` 的输出格式增加背景灰度、模式与纵向范围信息。

### 示例

- `examples/annotations.json` 按 `make_demo_shot.py` 的真实几何重新测量修正了多处坐标
  （此前有若干条指向元素外侧的空白处），并演示了 `dot_r` 与引线的用法。

## [1.0.0] - 2026-10-10

首个正式版本。

- 编号圆点标注图 PNG（含右侧分组图例面板与每块区域的功能说明）
- 单文件自包含交互式 HTML（悬停编号 ↔ 图例双向高亮，点击互相滚动定位）
- 一份 `annotations.json` 同时驱动两种交付物
- `group_notes` 区域级说明、`label_x`/`label_y` 圆点位置微调
- 可复现 demo：`examples/make_demo_shot.py` 生成模拟截图，无需自备素材
- `references/` 提供字段说明与常见界面部件中英对照

[1.0.1]: https://github.com/han719307-dotcom/screenshot-ui-explainer/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/han719307-dotcom/screenshot-ui-explainer/releases/tag/v1.0.0
