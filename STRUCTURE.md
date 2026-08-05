# 中山资源交易平台监控 Skill 目录结构

## 项目布局

```
zhongshan-monitor/
│
├── skill.md                          # Skill 定义和文档
├── README.md                         # 使用指南（详细）
├── STRUCTURE.md                      # 项目结构说明（本文件）
│
├── scripts/                          # Python 脚本目录
│   ├── __init__.py                   # Python 包初始化
│   ├── monitor.py                    # 核心监控逻辑
│   ├── crawler.py                    # 平台爬虫 & HTML 解析
│   ├── feishu_notifier.py           # 飞书通知集成
│   └── cron_handler.py              # OpenClaw 定时任务处理
│
├── config/                           # 配置文件目录
│   ├── platform-config.json         # 平台配置
│   └── feishu.json                  # 飞书机器人配置
│
├── memory/                           # 数据存储目录
│   ├── last-check.json              # 最新检查结果
│   └── archive/                     # 历史检查记录
│       ├── check_2026-03-17T08-30-00.json
│       ├── check_2026-03-17T12-00-00.json
│       └── check_2026-03-17T20-30-00.json
│
├── logs/                             # 日志目录
│   ├── monitor_20260317.log
│   ├── monitor_20260316.log
│   └── monitor_20260315.log
│
└── run.py                            # 启动脚本（根目录）
```

## 文件说明

### 核心文件

| 文件 | 说明 | 用途 |
|------|------|------|
| `monitor.py` | 监控逻辑引擎 | 主程序，负责完整的监控流程 |
| `crawler.py` | 平台爬虫 | 解析平台 HTML，提取项目列表 |
| `feishu_notifier.py` | 飞书通知 | 发送检查结果到飞书 |
| `cron_handler.py` | 定时任务 | OpenClaw 心跳机制集成 |

### 配置文件

| 文件 | 说明 | 编辑频率 |
|------|------|---------|
| `platform-config.json` | 监控配置（URL、关键词等） | 低（仅需初始化） |
| `feishu.json` | 飞书机器人配置 | 低（初始配置后基本不变） |

### 数据存储

| 目录 | 说明 | 保留期限 |
|------|------|---------|
| `memory/last-check.json` | 最新检查（用于增量对比） | 永久（不删除） |
| `memory/archive/` | 历史检查记录 | 建议保留90天 |
| `logs/` | 执行日志 | 建议保留30天 |

## 工作流程

```
用户/定时触发
    ↓
run.py 启动脚本
    ↓
monitor.py (ZhongshanMonitor 类)
    ├── fetch_platform_projects()      [使用 crawler.py]
    │   ↓
    │   crawler.py (爬虫)
    │   ├── fetch_and_parse_platform()
    │   ├── extract_projects_from_html()
    │   └── parse_platform_response()
    │
    ├── filter_by_keywords()            [关键词筛选]
    ├── load_last_check()              [加载历史记录]
    ├── detect_new_projects()          [增量检测]
    ├── save_check_result()            [保存结果]
    │
    └── send_feishu_notification()     [使用 feishu_notifier.py]
        ↓
        feishu_notifier.py (FeishuNotifier 类)
        └── 发送到飞书
```

## 定时任务集成

### OpenClaw 配置

三班制定时任务配置在 WorkBuddy 中：

```
任务ID: 4e9fda32-1a6b-4e5d-b022-1005a3bb31bd
班次: 早班
时间: 08:30
命令: python cron_handler.py --shift 早班

---

任务ID: f9bdacfd-6bf7-4252-aa5f-5688403c0d11
班次: 午班
时间: 12:00
命令: python cron_handler.py --shift 午班

---

任务ID: afcf0249-f6a5-4899-a8ba-9635b0701ed7
班次: 晚班
时间: 20:30
命令: python cron_handler.py --shift 晚班
```

### cron_handler.py 执行流程

```
OpenClaw 心跳 (定时触发)
    ↓
cron_handler.py
    ├── CronTaskRunner.get_current_shift()     [获取班次]
    ├── CronTaskRunner.run_check()             [执行监控]
    │   ↓
    │   monitor.py (完整监控流程)
    │
    └── CronTaskRunner.log_result()            [记录日志]
```

## 使用场景

### 场景1: 手动测试

```bash
cd ~/.workbuddy/skills/zhongshan-monitor
python run.py --shift 早班 --test
```

### 场景2: 启用飞书通知

```bash
python run.py --shift 早班 --notify
```

### 场景3: 首次配置飞书

```bash
python run.py --setup-feishu
```

### 场景4: 自动定时执行

由 OpenClaw 定时触发 `cron_handler.py`

## 数据流向

```
┌─ last-check.json (上次检查结果)
│  └─ 用于增量对比 ─→ 识别新增项目
│
├─ 平台 HTML
│  └─ 爬虫解析 ─→ 提取项目列表
│
└─ 新增项目
   └─ 飞书通知 ─→ 用户收到消息
   └─ 存储为新的 last-check.json
   └─ 归档到 archive/ 目录
   └─ 记录到 logs/ 目录
```

## 扩展点

### 1. 添加新的平台监控

复制此 Skill 目录，修改：
- `config/platform-config.json` 中的 URL 和关键词
- `scripts/crawler.py` 中的 HTML 解析规则

### 2. 支持新的通知渠道

编辑 `scripts/feishu_notifier.py`，增加新类：
```python
class DingtalkNotifier:
    def send_notification(self, ...):
        # 钉钉通知实现
```

### 3. 增加数据分析功能

在 `scripts/monitor.py` 中扩展：
```python
def analyze_projects(self, projects):
    # 数据分析逻辑
```

## 环境要求

- Python 3.7+
- 依赖库：requests, beautifulsoup4（可选，有本地实现）
- 网络访问：平台 URL、飞书 API
- 存储空间：通常 < 10MB/月

## 性能指标

| 指标 | 目标 | 实际 |
|------|------|------|
| 单次执行时间 | < 30s | ~5-10s |
| 内存占用 | < 50MB | ~20-30MB |
| 存储增长 | < 1MB/天 | ~0.1-0.5MB/天 |

## 维护清单

- [ ] 每月检查一次 `memory/archive/` 是否过大（建议 > 100MB 时清理）
- [ ] 检查 `logs/` 目录是否超过 50MB（建议定期压缩）
- [ ] 每季度更新一次平台 HTML 解析规则（如平台改版）
- [ ] 验证飞书 Webhook 连接性（每月一次）

---

Last Updated: 2026-03-17
