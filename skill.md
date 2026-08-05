---
name: zsjypt-monitor
version: 3.1.0
description: >-
  中山市公共资源交易平台（zsjypt.cn）招标信息监控工具：抓取「建设工程」「政府采购」共 14 个栏目的新上架项目，
  支持关键词追踪、多平台推送（飞书/企业微信/钉钉）与可视化看板。当用户需要「监控中山公共资源交易新项目 /
  按公司名追踪中标与招标动态 / 生成每日看板 / 设定工作日自动化汇报」时使用。
triggers:
  - 中山公共资源
  - zsjypt
  - 招标监控
  - crab监控
  - 公共资源交易
  - 中山平台监测
agent_created: true
metadata:
  skill_type: monitor
  cli_entry: scripts/crab-monitor.py
  dashboard_entry: scripts/make_dashboard.py
  config_dir: config/
  pure_stdlib: false
  dependencies: [requests, beautifulsoup4]
  platform: https://www.zsjypt.cn
---

# 中山公共资源交易平台监控（zsjypt-monitor）

监控 https://www.zsjypt.cn 的建设工程 + 政府采购全栏目，产出可刷新的可视化仪表盘，并支持按公司名追踪。

## 最高优先级规则

- `scripts/crab-monitor.py` 是唯一实现与唯一事实源；`scripts/make_dashboard.py` 仅做展示层。
- 输出即事实：不得自行摘要、改写、重排、合并分类或补造项目。
- 普通汇报覆盖**当日**新增；若 `config/user-config.json` 设了 `keywords`，只报标题含这些词的项目，否则全量汇报。
- 追踪按关键词全文匹配，覆盖全部来源与全部类型。
- 自动化最终响应必须原样返回脚本 stdout / 仪表盘状态，不写二次确认或摘要。
- **密钥绝不打印**：webhook / AI key 只报「是否已配置 + 来源」，绝不输出值。

## 快速执行

```bash
cd <repo>/scripts
python crab-monitor.py            # 抓取 + 存快照 + 打印文本报告
python make_dashboard.py          # 更新 reports/live/dashboard-data.js（仪表盘接入新数据）
```

运行环境：Python 3.10+，依赖 `requests`、`beautifulsoup4`（见「依赖」）。WorkBuddy 管理 venv 可直接用其 `python.exe` 运行；也可在任意含依赖的 Python 环境执行，无需特定绝对路径。

## 监控架构

| 组件 | 路径 | 说明 |
|------|------|------|
| 主脚本 | `scripts/crab-monitor.py` | Python3，requests+BS4，14 栏目抓取 |
| 仪表盘生成器 | `scripts/make_dashboard.py` | 读快照 → 更新 `reports/live/dashboard-data.js` |
| 常驻面板 | `reports/live/dashboard.html` | 外壳仅首次创建，架构恒定（JS 读 data.js 渲染） |
| 面板数据 | `reports/live/dashboard-data.js` | 每次抓取**只更新此文件**，HTML 不重建 |
| 上次全量 | `scripts/memory/zsjypt_last.json` | 增量对比基线 + 中标详情持久化（运行时生成，不提交） |
| 追踪状态 | `scripts/memory/zsjypt_tracking.json` | 关注关键词及已见 key（运行时生成，不提交） |
| 推送配置 | `config/notify.json` | 飞书/企业微信/钉钉 Webhook（占位符，填地址即启用） |
| 推送模块 | `scripts/notify.py` | 自动适配三平台报文；`--guide/--status/--test` |
| 用户私有配置 | `config/user-config.json` | 过滤关键词 + 追踪词（首轮 init 生成，不提交） |

> 本 skill 只认 `crab-monitor.py`、`make_dashboard.py`、`notify.py`；其余遗留脚本均已移除。

## 栏目与抓取机制

14 个监控栏目及其 `node_id`、列表 API 的调用方式，以及去重/主键、中标详情、增量对比、追踪检查、代理绕过等机制，详见 **`references/columns.md`**。

## 可视化仪表盘（常驻面板）

- 架构：`reports/live/dashboard.html`（外壳仅首次创建）→ 内含 JS 读 `dashboard-data.js` 渲染。
- 每次抓取**只更新 `dashboard-data.js`**，HTML 不重建；新清单直接接入面板。
- 面板内容随用户配置变动：今日清单按 `user-config.json` 的 `keywords` 过滤；meta 显示过滤范围；footer 显示已启用推送平台；追踪区块读 `zsjypt_tracking.json`。
- 用法：
  - `python make_dashboard.py` —— 更新 live 数据（默认今天）
  - `python make_dashboard.py 2026-07-29` —— 指定日期
  - `python make_dashboard.py --standalone` —— 生成自包含单文件 HTML 到 `reports/YYYY-MM-DD/dashboard.html`
  - `python make_dashboard.py --rebuild` —— 强制重建外壳模板

## 可直开链接（CloudStudio 部署）

要求仪表盘必须是可直接打开的链接。部署流程与自动化集成详见 **`references/deploy.md`**。

## 多平台推送

支持飞书 / 企业微信（即微信）/ 钉钉群机器人。首次配置引导、Webhook 获取与报文适配详见 **`references/notify.md`**。脚本末尾在生成报告后自动推送至已配置平台；未配置则跳过，不影响主流程。

## 追踪关键词与首轮配置

```bash
cd <repo>/scripts
python crab-monitor.py init        # 交互式填写过滤关键词 + 追踪公司名，写入 user-config.json 并建追踪
python crab-monitor.py track 示例公司   # 添加关注
python crab-monitor.py untrack 示例公司 # 移除关注
python crab-monitor.py list       # 查看关注列表
```

追踪关键词在**首次配置时由用户设定**，保存在私有配置（`config/user-config.json`，已被 .gitignore 排除，不随仓库公开）。也可把 `config/user-config.example.json` 复制为 `config/user-config.json` 直接填写（`keywords`=普通汇报过滤项，`track_terms`=追踪关键词）。首次运行若缺该文件，脚本提示并以全量汇报降级，不阻塞自动化。

## 自动化（已部署 · 工作日 ACTIVE）

| 任务 | 时间 | 行为 |
|------|------|------|
| 午班 | 工作日 12:00 | 抓取 → 更新 live data.js → 生成 standalone → 部署 CloudStudio → 写链接 → 返回可直开链接 |
| 晚班 | 工作日 18:00 | 同上（有效汇报窗口，平台新条目多集中在 14:00–17:30） |

自动化 prompt 要点：venv python 跑 `crab-monitor.py` → 跑 `make_dashboard.py`（只更新 data.js）→ 跑 `make_dashboard.py 当天 --standalone` → `workbuddy_cloudstudio_deploy` 部署 → 链接写入 `reports/live/dashboard_link.txt` → 返回摘要+链接。推送由 `crab-monitor.py` 末尾按 `config/notify.json` 自动执行。

## 依赖

- `requests`、`beautifulsoup4`（Python 3.10+）。
- 无需 API key（平台公开数据）。
- 多平台推送可选（填 `config/notify.json` 的 webhook；支持飞书/企业微信/钉钉，自动适配）。

## 注意事项 / 已知问题

- 非工作日（周末/假期）平台无更新，跑出来是空报告。
- 中标详情为同步抓取（逐个 requests.get），量大时略慢（整轮约 3~26 秒）。
- 平台偶发 SSL 抖动（`SSLEOFError`）：脚本跳过失败栏目继续；强制直连后主要风险已消除。
- `zsjypt_last.json` 每次正式运行更新（增量对比基线）。
- 推送按需：未填 webhook 时只产出报告/更新面板，不推送；填好即自动推送。

## 维护

- 脚本逻辑以 `crab-monitor.py` 为准，勿在别处重写。
- 新增监控栏目：在 `crab-monitor.py` 的 `SOURCES` 列表加一项（name + node_id），仪表盘自动适配。
- 面板样式调整：改 `make_dashboard.py` 内 `SHELL_HTML` 常量（仅影响外壳，更新后 `--rebuild` 重建一次）。
