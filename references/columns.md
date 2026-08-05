# 监控栏目与抓取机制

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

新增栏目：在 `crab-monitor.py` 的 `SOURCES` 列表追加 `{name, node_id}` 即可，仪表盘按 `SOURCE_ORDER` 自动排序。

## 列表 API 调用

```
POST https://www.zsjypt.cn/pageList
Content-Type: application/x-www-form-urlencoded
Body: offset=1&limit=30&nodeId=<node_id>
```

- 只取第一页 30 条，不翻页（规避平台翻页重复）。
- 返回 `{code:0, data:{total, rows:[...]}}`；字段：`arab01`=ID、`arab04`=标题、`arab32`=发布时间、`arab25`=报名截止、`arab26`=开标时间。
- 快照内已归一化为 `{key,title,date,pub_at,source,url,node_id,aid}`，勿再依赖原始 `arabXX` 字段。

## 去重 / 主键

`key = {node_id}-{arab01}`，跨天增量对比基线为 `scripts/memory/zsjypt_last.json`。

## 中标详情持久化

对所有 `node_id=61`（中标信息）条目持久化抓取中标单位/中标价/日期——优先复用历史快照，仅新条目才发请求，避免跨天重存快照丢失历史中标数据。

## 增量对比

用 `scripts/memory/zsjypt_last.json` 做跨天基线；每次正式运行后更新（有数据才保存，空结果不覆盖基线）。

## 追踪检查

对全部 14 栏目全量数据，按关键词标题全文匹配，检出不在 `seen_keys` 中的新项目（覆盖全部类型）。状态存 `scripts/memory/zsjypt_tracking.json`，记录每个关键词的已见 key 集合。

## 代理绕过

环境可能注入不稳定系统代理（如 `127.0.0.1:11719`，间歇拒绝连接），导致全栏目失败。脚本在每次 `requests` 调用强制 `proxies={'http':None,'https':None}` 直连规避。若再现 `SSLEOFError` 类抓取失败，优先怀疑隧道/代理出口而非脚本。
