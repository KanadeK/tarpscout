# TarpScout 简体中文说明

TarpScout 是一个完全离线的营地天幕搭建求解器。你输入现场测得的支撑点、
可绑高度、可打钉区域、圆形禁入区、必须被覆盖的矩形区域、天幕尺寸，以及手里
每根风绳的实际长度；它会在有限网格中搜索 A 字形和单坡形方案，精确分配整根
风绳，并在无解时说明究竟是哪条约束阻断了方案。

它不是画一张示意界面的空壳：求解器会真实计算几何、覆盖、禁入碰撞、地钉位置、
风绳需求与候选排序，输出稳定 JSON、CSV、带标签 SVG 和无脚本 HTML。

> 输出只是规划证据，不是结构、风雪、土壤、树木、杆件、绳结、地钉或布料安全
> 认证。到现场后必须复核尺寸、锚点与装备说明。

## 快速体验

```powershell
git clone https://github.com/KanadeK/tarpscout.git
cd tarpscout
uv sync --locked
uv run tarpscout demo build/demo
```

demo 会实际运行四个场景：

- `pine-gap`：找到 A 字形方案；
- `creek-lean-to`：找到单坡形方案；
- `fire-ring`：因为火圈禁入区而无解；
- `short-cords`：因为现有风绳过短而无解。

## 使用自己的测量数据

复制 [pine-gap 示例](../examples/pine-gap.site.json)，修改其中的米制坐标和长度：

```powershell
uv run tarpscout validate examples/pine-gap.site.json
uv run tarpscout solve examples/pine-gap.site.json --output build/pine-gap
```

找到方案时会生成：

- `<名称>.report.json`：候选、搜索统计、拒绝原因和修复建议；
- `<名称>.lines.csv`：每根脊线/风绳的端点、需求长度、分配绳段和余量；
- `<名称>.plan.svg`：带支撑点和地钉标签的俯视图；
- `<名称>.elevation.svg`：脊高、边高、坡度和地钉退距；
- `<名称>.report.html`：内嵌两张 SVG 的自包含无脚本报告。

有效但无解时只写诊断 JSON，退出码为 `1`；输入或文件错误退出码为 `2`；成功
求解、验证或 demo 退出码为 `0`。`no_solution` 只表示在当前输入和有限搜索网格
内无解，不代表现实中绝对无法搭建。

## 输入与修复

完整字段说明见 [input-format.md](input-format.md)，拒绝原因与逐项修复方法见
[troubleshooting.md](troubleshooting.md)。常见修复方向包括：扩大或移动可打钉区、
挪开禁入物/覆盖目标、调整脊高和边高、换更长风绳、减小结绳余量，或在明确理解
计算量后调大 `max_search_states`。

## 本地验收

```powershell
uv run python scripts/check.py
```

该命令会检查 90% 以上分支覆盖率、格式、lint、严格类型、重复 demo 字节一致、
wheel/sdist、demo ZIP、干净 wheel 安装和安装后命令。失败时修根因，不要跳过测试
或降低门槛。

## 明确不做

v0.1.0 不计算布料下垂/悬链线、风雪载荷、土壤承载、GPS 地形、天气，也不处理
自由形状天幕、帐篷、吊床或在线导航。项目不需要账号，不上传营地数据，运行时无
第三方依赖。
