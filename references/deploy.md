# 可直开链接（CloudStudio 部署）

用户要求：仪表盘报告必须是**可直接打开的链接**，不是本地路径。

## 部署流程（自动化已内置，也可手动）

1. `make_dashboard.py 当天日期 --standalone` 生成自包含 HTML → `reports/YYYY-MM-DD/dashboard.html`（数据内联，不依赖外部 `dashboard-data.js`）。
2. 用 `workbuddy_cloudstudio_deploy` 部署该目录（entry=`dashboard.html`）→ 拿到 https 分享链接。
3. 链接写入 `reports/live/dashboard_link.txt`（覆盖式，作为最新链接记录）。

## 自动化集成

工作日 12:00 / 18:00 自动化跑完会**自动重新部署**并更新 `dashboard_link.txt`，返回一句话摘要 + 可直开链接。

## 注意事项

- CloudStudio 每次部署是新 sandbox，**链接会随部署变更**；以 `reports/live/dashboard_link.txt` 中记录为准（或向 Agent 问"最新链接"）。
- 管理已发布应用：**「设置 - 数据管理 - 我发布的应用」**。
- 若仅需本地查看，直接浏览器打开 `reports/live/dashboard.html` 刷新即可（file:// 下 `<script src>` 同目录加载正常）。
