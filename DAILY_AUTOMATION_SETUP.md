# WorkBuddy 自动化配置
# 每天下午 3 点运行中山平台监测，并将结果发送到飞书

## 任务名称
自动监测中山平台 - 每日下午3点

## 任务描述
每天下午 3 点自动执行中山平台监测：
1. 检测新项目并记录
2. 检测已跟踪项目的变化
3. 将完整报告发送到飞书

## 执行命令
```bash
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor && python daily_scheduler.py
```

## 执行频率
- 时间: 每天下午 3 点 (15:00)
- 格式: FREQ=DAILY;BYHOUR=15;BYMINUTE=0
- 时区: Asia/Shanghai (北京时间)

## 配置步骤

### 第 1 步：配置飞书 Webhook URL

首先，你需要获取飞书的 Webhook URL 并配置到系统中：

**获取飞书 Webhook URL 的步骤：**
1. 打开飞书客户端
2. 找到或创建一个群聊/频道
3. 右键点击群聊 → 管理 → 机器人
4. 点击 "添加应用" → "添加群机器人"
5. 选择或创建一个机器人
6. 复制 Webhook URL

**配置 Webhook URL：**
```bash
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
python scripts/feishu_sender.py --setup "<你的 Webhook URL>"
```

### 第 2 步：测试配置

发送测试消息确保配置正确：

```bash
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
python scripts/feishu_sender.py --test
```

如果收到飞书消息，说明配置成功！

### 第 3 步：创建 WorkBuddy 自动化任务

在 WorkBuddy 中创建自动化任务：

**方式 A: 使用命令行创建**
```bash
workbuddy automation create \
  --name "中山平台每日监测" \
  --prompt "运行 C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor\daily_scheduler.py" \
  --schedule "FREQ=DAILY;BYHOUR=15;BYMINUTE=0" \
  --cwd "C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor"
```

**方式 B: 使用 WorkBuddy UI 创建**
1. 打开 WorkBuddy 设置
2. 找到 "自动化" 或 "任务计划" 选项
3. 新建自动化
4. 配置如下信息：
   - 名称: "中山平台每日监测"
   - 运行命令: `python daily_scheduler.py`
   - 执行路径: `C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor`
   - 时间表: 每天 15:00 (下午3点)
   - 启用自动发送飞书通知

## 运行流程

每天 15:00（下午3点）系统将自动：

```
15:00:00
  ↓
启动监测脚本
  ├─ 获取平台所有项目
  ├─ 检测新项目
  ├─ 检测跟踪项目的变化
  └─ 保存数据
  ↓
生成监测报告
  ├─ 新项目清单
  ├─ 跟踪项目更新
  └─ 异常警告
  ↓
发送飞书消息
  ├─ 标题: 每日中山平台监测报告
  └─ 内容: 完整的监测结果
  ↓
任务完成
  └─ 等待下一天 15:00
```

## 监测报告示例

你将在飞书收到如下格式的消息：

```
【每日中山平台监测报告】
发送时间: 2026-03-18 15:00:00

【新项目】(2 个)
──────────────────────────────────
[1] 医药城项目
    栏目: 产业园
    发布: 2026-03-18 14:30:00
    URL: https://...

[2] 翠锦路项目
    栏目: 基础设施
    发布: 2026-03-18 14:45:00
    URL: https://...

【跟踪项目更新】(1 项)
──────────────────────────────────
[proj_001] 中心四路
  * 发布澄清: 关于采购计划的补充说明
  * 更新答疑: 新增 3 条常见问题

【监测完成】 新项目: 2 | 变化: 1
```

## 故障排除

### 问题 1: 显示 "飞书 Webhook URL 未配置"

**解决方案：**
```bash
python scripts/feishu_sender.py --setup "<你的 Webhook URL>"
```

### 问题 2: 飞书消息发送失败

**检查步骤：**
1. 确认 Webhook URL 是否正确
2. 运行测试命令: `python scripts/feishu_sender.py --test`
3. 检查网络连接
4. 查看 feishu.json 配置文件是否存在

### 问题 3: 监测任务没有在规定时间运行

**检查步骤：**
1. 确认 WorkBuddy 自动化任务已启用
2. 检查系统时间是否正确
3. 查看 WorkBuddy 的自动化日志

## 高级配置

### 修改执行时间

如果你想改成其他时间，比如每天早上 9 点：

```bash
# 编辑自动化任务的时间表
# 从 FREQ=DAILY;BYHOUR=15;BYMINUTE=0
# 改为 FREQ=DAILY;BYHOUR=9;BYMINUTE=0
```

### 添加多个通知渠道

你可以修改 `daily_scheduler.py` 来支持多个通知渠道：

```python
# 发送到飞书
sender.send_daily_report(new_projects, tracked_changes)

# 发送到邮件
email_sender.send_report(new_projects, tracked_changes)

# 保存到本地文件
save_report_to_file(new_projects, tracked_changes)
```

### 自定义报告格式

编辑 `feishu_sender.py` 的 `send_daily_report` 方法来自定义报告格式。

## 维护清单

- [ ] 已配置飞书 Webhook URL
- [ ] 已测试飞书消息发送
- [ ] 已在 WorkBuddy 中创建自动化任务
- [ ] 已验证定时任务在规定时间运行
- [ ] 已配置要监测的项目列表
- [ ] 已测试完整的监测和通知流程

## 支持

如有问题，请检查以下文件：
- `config/feishu.json` - 飞书配置
- `memory/last-check.json` - 上次检查数据
- `memory/tracked_projects.json` - 跟踪项目列表
- `memory/project_history.json` - 项目历史记录
