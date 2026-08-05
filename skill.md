---
name: zsjypt-monitor
version: 3.1.0
description: 中山市公共资源交易平台（zsjypt.cn）监控 — 运行 scripts/crab-monitor.py 抓 14 栏目全量，生成常驻可视化仪表盘（reports/live/），工作日 12:00/18:00 自动化；追踪指定公司关键词
triggers:
  - 中山公共资源
  - zsjypt
  - 招标监控
  - crab监控
  - 公共资源交易
  - 中山平台监测
---

# 中山公共资源交易平台监控 v3.1（固化版）

> 监控 https://www.zsjypt.cn 的建设工程 + 政府采购全栏目，产出可刷新的可视化仪表盘，并支持按公司名追踪。

## 最高优先级规则

- `scripts/crab-monitor.py` 是唯一实现与唯一事实源；`scripts/make_dashboard.py` 仅做展示层。
- Agent 不得擅自摘要、改写、重排、合并分类或补造项目；脚本输出即事实。
- 普通汇报覆盖**当日全部栏目**新增（脚本当前不过滤设计/勘察，全量汇报）。
- 追踪项目按关键词全文匹配，覆盖全部来源与全部类型。
- 自动化最终响应必须原样返回脚本 stdout / 仪表盘状态；不要写二次确认或摘要。

## 快速执行

```bash
cd scripts
python crab-monitor.py            # 抓取 + 存快照 + 打印文本报告
python make_dashboard.py          # 更新 reports/live/dashboard-data.js（仪表盘接入新数据）
```

运行环境：WorkBuddy 管理 venv
`G:\2026 赚大钱\.workbuddy\binaries\python\envs\default\Scripts\python.exe`
（已装 requests 2.34.2 + beautifulsoup4 4.15.0）

## 监控架构

| 组件 | 路径 | 说明 |
|------|------|------|
| 主脚本 | `scripts/crab-monitor.py` | Python3，requests+BS4，14 栏目全量抓取 |
| 仪表盘生成器 | `scripts/make_dashboard.py` | 读快照 → 更新 `reports/live/dashboard-data.js` |
| 常驻面板 | `reports/live/dashboard.html` | 外壳，仅首次创建，架构恒定（JS 读 data.js 渲染） |
| 面板数据 | `reports/live/dashboard-data.js` | 每次抓取**只更新此文件**，HTML 不重建 |
| 上次全量 | `scripts/memory/zsjypt_last.json` | 抓取全量数据（增量对比基线 + 中标详情持久化） |
| 追踪状态 | `scripts/memory/zsjypt_tracking.json` | 关注关键词及已见 key |
| 推送配置 | `config/notify.json` | 飞书/企业微信/钉钉 Webhook（占位符，填地址即启用） |
| 推送模块 | `scripts/notify.py` | 自动适配三平台报文格式；`--guide/--status/--test` |

> ⚠️ `scripts/` 下其余 `*.py`（monitor.py / final_monitor*.py / api.py / crawler.py / run_*.py / tracking_manager.py / feishu_*.py 等）均为 **v1.0 遗留文件，已废弃**，请勿使用。本 skill 只认 `crab-monitor.py` 与 `make_dashboard.py`。

## 14 个监控栏目

| 栏目 | node_id |
|------|---------|
| 建设工程-招标计划 | 209 |
| 建设工程-招标文件提前公示 | 210 |
| 建设工程-招标公告 | 58 |
| 建设工程-答疑、澄清 | 59 |
| 建设工程-评标结果公示 | 208 |
| 建设工程-中标候选人公示 | 60 |
| 建设工程-中标信息 | 61 |
| 建设工程-项目公告 | 107 |
| 建设工程-招投标公开信息 | 172 |
| 政府采购-采购公告 | 53 |
| 政府采购-答疑、更正公告 | 54 |
| 政府采购-中标公告 | 115 |
| 政府采购-废标公告 | 138 |
| 政府采购-采购需求公示 | 160 |

## 核心逻辑

1. **列表抓取**：POST `https://www.zsjypt.cn/pageList` → `{offset:1, limit:30, nodeId:X}`，只取第一页 30 条（规避平台翻页重复）。
2. **去重/主键**：`key = {node_id}-{arab01}`。
3. **中标详情**：对所有 `node_id=61`（中标信息）条目持久化抓取中标单位/中标价/日期——优先复用历史快照，仅新条目才发请求。
4. **增量对比**：用 `scripts/memory/zsjypt_last.json` 做跨天基线。
5. **追踪检查**：对全部 14 栏目全量数据，按关键词标题全文匹配，检出不在 seen_keys 中的新项目（覆盖全部类型）。
6. **代理绕过**：脚本强制直连 `proxies={'http':None,'https':None}`，避免环境注入的不稳定系统代理（127.0.0.1:11719）导致抓取失败。

## 可视化仪表盘（常驻面板模式）

- 架构：`reports/live/dashboard.html`（外壳，仅首次创建）→ 内含 JS 读 `dashboard-data.js` 渲染。
- 每次抓取**只更新 `dashboard-data.js`**，HTML 不重建；新清单直接接入面板。
- 面板含：KPI（今日新增 / 涉及栏目 / 追踪新增）、栏目分布条形图、分栏项目卡片（中标单位·中标价高亮）、关注公司追踪状态，浅色主题。
- 用法：
  - `python make_dashboard.py` —— 更新 live 数据（默认今天）
  - `python make_dashboard.py 2026-07-29` —— 指定日期
  - `python make_dashboard.py 2026-07-29 --standalone` —— 生成**自包含单文件** HTML（数据内联）到 `reports/YYYY-MM-DD/dashboard.html`，用于部署/分享（不依赖外部 dashboard-data.js）
- 查看：浏览器打开 `reports/live/dashboard.html`，刷新即看最新（file:// 下 `<script src>` 同目录加载正常）。

## 可直开链接（CloudStudio 部署）

> 用户要求：仪表盘报告必须是**可直接打开的链接**，不是本地路径。

- 部署流程（自动化已内置，也可手动）：
  1. `make_dashboard.py 当天日期 --standalone` 生成自包含 HTML → `reports/YYYY-MM-DD/dashboard.html`
  2. 用 `workbuddy_cloudstudio_deploy` 部署该目录（entry=dashboard.html）→ 拿到 https 分享链接
  3. 链接写入 `reports/live/dashboard_link.txt`（覆盖式，作为最新链接记录）
- 自动化（工作日 12:00/18:00）跑完会**自动重新部署**并更新 `dashboard_link.txt`，返回一句话摘要 + 可直开链接。
- ⚠️ CloudStudio 每次部署是新 sandbox，**链接会随部署变更**；以 `reports/live/dashboard_link.txt` 中记录为准（或向我问"最新链接"）。
- 管理已发布应用：**「设置 - 数据管理 - 我发布的应用」**。


## 多平台推送（首次配置引导）

> 本 skill 支持把每日报告推送到 **飞书 / 企业微信（即微信）/ 钉钉** 群机器人。微信个人号无官方推送接口，统一走企业微信群机器人。

**首次加载或后续需增配推送时**，Agent 必须主动弹出配置引导（不要静默跳过）：

```bash
cd scripts
python notify.py --guide     # 弹出配置引导：说明三个平台如何获取 Webhook
```

- 引导内容见 `scripts/notify.py` 的 `show_guide()`，涵盖：飞书 / 企业微信 / 钉钉各自的 Webhook 获取路径、加签 secret 填写、以及 `config/notify.json` 与环境变量两种配置方式。
- **自动适配**：`config/notify.json` 三个平台各留一个 Webhook 占位符；用户**只需把对应地址填进去，无需改任何逻辑**——脚本自动按平台拼装报文并推送，未填的平台自动跳过。
- 配置模板：

```json
{
  "feishu":   { "webhook": "（填飞书自定义机器人 Webhook）", "secret": "" },
  "wecom":    { "webhook": "（填企业微信群机器人 Webhook，即推到微信）", "secret": "" },
  "dingtalk": { "webhook": "（填钉钉自定义机器人 Webhook）", "secret": "" }
}
```

- 验证与试用：`python notify.py --status`（看已启用哪些）、`python notify.py --test`（发测试消息）。
- 自动化（午班/晚班）跑完会在生成仪表盘**之后**自动推送报告到所有已配置平台；未配置则不推送、不影响主流程。
- 旧 `config/feishu.json` 已弃用，统一改用 `config/notify.json`。

## 追踪关键词

```bash
cd scripts
python crab-monitor.py track 中誉        # 添加关注
python crab-monitor.py untrack 中誉       # 移除关注
python crab-monitor.py list               # 查看关注列表
```

追踪：添加关键词后，只要该关键词下有新公告（任何栏目），报告的「关注项目更新」部分高亮显示。内部用 `zsjypt_tracking.json` 记录已见 key，增量对比。

当前已初始化（与 WSL 版一致）：**中联合创、广东行远、深圳华粤、中誉**。

## 自动化（已部署 · 工作日 ACTIVE）

| 任务ID | 名称 | 时间 | 行为 |
|--------|------|------|------|
| automation-1785333223597 | 午班 | 工作日 12:00 | 抓取 → 更新 live data.js → 生成 standalone → 部署 CloudStudio → 写链接 → 返回可直开链接 |
| automation-1785333224336 | 晚班 | 工作日 18:00 | 同上 |

自动化 prompt 要点（与「可直开链接」章节一致）：
1. venv python 跑 `crab-monitor.py`（抓取+存快照+打印文本）
2. 同 venv 跑 `make_dashboard.py`（只更新 `reports/live/dashboard-data.js`，外壳仅首次建）
3. 跑 `make_dashboard.py 当天日期 --standalone`（生成自包含 HTML 到 `reports/YYYY-MM-DD/dashboard.html`）
4. 调用 `workbuddy_cloudstudio_deploy` 部署该目录（entry=dashboard.html）拿到 https 链接
5. 链接写入 `reports/live/dashboard_link.txt`（覆盖式更新）
6. 返回一句话摘要（今日新增 N / 涉及 M 栏目 / 追踪 K 条）+ 可直开仪表盘链接
7. 推送（按需）：crab-monitor.py 末尾在生成报告后自动推送至 `config/notify.json` 中已配置的飞书/企业微信/钉钉；未配置则跳过，不报错

## 已修复的问题（固化时确认）

| 问题 | 修复 |
|------|------|
| 环境注入不稳定系统代理 127.0.0.1:11719（间歇拒绝连接）致 14 栏目全失败 | `crab-monitor.py` 两处 requests 加 `proxies={'http':None,'https':None}` 强制直连 |
| 原 `load_last()` 写 `json.load(f)`（应为 `json.load(fh)`）致读快照崩 | 已修正 |
| 中标详情只在"当天"抓取，跨天重存快照丢失历史中标单位/价 | 改为对所有 `node_id=61` 持久化（复用历史快照，仅新条目抓取） |

## 依赖

- requests, beautifulsoup4（已装于 WorkBuddy 管理 venv）
- 无需 API key（平台公开数据）
- 多平台推送可选（需填 `config/notify.json` 的 webhook；支持飞书/企业微信/钉钉，自动适配）

## 注意事项 / 已知问题

- 非工作日（周末/假期）平台无更新，跑出来是空报告。
- 中标详情为同步抓取（逐个 requests.get），量大时略慢（整轮约 3~26 秒）。
- 平台偶发 SSL 抖动（`SSLEOFError`）：脚本跳过失败栏目继续，不影响整体；代理绕过后主要风险已消除。
- `zsjypt_last.json` 每次正式运行更新（增量对比基线）。
- 推送按需：未填 `config/notify.json` 的 webhook 时，自动化只产出报告文本/更新面板，不推送；填好地址即自动推送到对应平台群聊。

## 维护

- 脚本逻辑以 `crab-monitor.py` 为准，请勿在别处重写。
- 新增监控栏目：在 `crab-monitor.py` 的 `SOURCES` 列表加一项（name + node_id）即可，仪表盘自动适配。
- 面板样式调整：改 `make_dashboard.py` 内 `SHELL_HTML` 常量（仅影响外壳，更新后删除旧 `reports/live/dashboard.html` 让其重建一次）。
