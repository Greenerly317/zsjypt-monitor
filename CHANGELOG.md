# Changelog

本文件记录 zsjypt-monitor skill 的重要变更。格式参考 [Keep a Changelog](https://keepachangelog.com/)。

## [3.1.0] - 2026-08-05

### Added
- `scripts/doctor.py`：离线环境自检（Python 版本 / 依赖 / 脚本 / 配置模板 / 推送与关键词状态），密钥绝不打印。
- `requirements.txt`：`requests` + `beautifulsoup4` 依赖声明，便于复现安装。
- `references/` 目录：`columns.md`（14 栏目与抓取机制）、`deploy.md`（CloudStudio 部署）、`notify.md`（推送配置），将细节从 `skill.md` 拆出做渐进式披露。
- `.github/workflows/ci.yml`：推送时冒烟测试（安装依赖 + 跑 doctor）。
- `CHANGELOG.md`。

### Changed
- `skill.md` 合规化：frontmatter 补 `agent_created: true` 与 `metadata` 块；`description` 改为第三人称并写明触发场景；移除硬编码绝对路径，改为可移植说明；正文去除第二人称。
- 仪表盘去写死：`make_dashboard.py` 的今日清单按 `user-config.json` 的 `keywords` 过滤；meta/footer 动态显示过滤范围与推送状态（详见提交 `cb55dd0`）。

### Removed
- 清理 v1.0 遗留：9 个过时 `.md` 指南（START_HERE / QUICKSTART / STRUCTURE / CHECKLIST / OPENCLAW_INTEGRATION / AUTOMATION_SETUP_GUIDE / DAILY_AUTOMATION_SETUP / INTEGRATION_QUICKSTART / TRACKING_GUIDE）与多个遗留脚本（api / crawler / monitor / fetch_platform / run_* / tracking_manager / cron_handler 等），消除与"只用 crab-monitor.py"的自相矛盾。
- 移除未使用的 `config/platform-config.json`。

## [3.0.0] - 前期版本

- 自 WSL `crab-monitor` v3.0 迁移，14 栏目全量监控、中标详情持久化、追踪系统、常驻仪表盘、多平台推送与工作日自动化。
