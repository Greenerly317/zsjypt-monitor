# 🚀 中山平台每日自动化监测 - 完整设置指南

## 📋 概览

你将拥有一个**完全自动化的监测系统**：

```
每天下午 15:00 (3点)
  ↓
自动执行监测
  ├─ 检测新项目
  ├─ 检测跟踪项目变化
  └─ 生成报告
  ↓
自动发送到飞书
  ├─ 新项目清单
  ├─ 变化通知
  └─ 异常警告
  ↓
完成 ✓
```

---

## ⚙️ 一键设置（推荐）

如果你使用 WorkBuddy，最简单的方式是直接创建自动化：

### 步骤 1: 获取飞书 Webhook URL

#### 在飞书中创建群机器人：

1. 打开**飞书客户端** → 点击某个群聊
2. 点击群名称 → **群设置** → **群机器人** → **添加机器人**
3. 选择 **自定义机器人**
4. 填写信息：
   - 机器人名称: `中山平台监测`
   - 描述: `每日中山平台监测报告`
5. **复制 Webhook URL**（类似 `https://open.feishu.cn/open-apis/bot/v2/hook/xxx`）

### 步骤 2: 配置 Webhook URL

运行命令配置 Webhook：

```bash
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
python scripts/feishu_sender.py --setup "你复制的 Webhook URL"
```

输出应该显示：
```
[OK] 飞书 Webhook URL 已保存
```

### 步骤 3: 测试飞书集成

```bash
python scripts/feishu_sender.py --test
```

你应该在飞书群里收到一条测试消息，显示当前时间。

### 步骤 4: 创建自动化任务

在 WorkBuddy 中执行以下命令来创建自动化：

```bash
# 方式 A: 如果你有 WorkBuddy CLI 工具
workbuddy automation create \
  --name "中山平台每日监测" \
  --prompt "运行中山平台监测脚本" \
  --schedule "FREQ=DAILY;BYHOUR=15;BYMINUTE=0" \
  --cwd "C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor"
```

或者让我直接创建自动化配置...

---

## 🔧 Windows 原生定时任务设置

如果你想使用 **Windows 系统自带的任务计划程序**（不依赖 WorkBuddy）：

### 方式 A: 自动创建（推荐）

打开 PowerShell（**以管理员身份**），运行：

```powershell
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Create
```

输出：
```
[创建定时任务]
[OK] 定时任务创建成功
  任务名称: 中山平台每日监测
  执行时间: 每天下午 3 点 (15:00)
  执行脚本: C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor\daily_scheduler.py
  工作目录: C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
```

### 方式 B: 手动创建

1. 打开 **Windows 任务计划程序**
2. 右键 **任务计划程序库** → **创建基本任务**
3. 名称: `中山平台每日监测`
4. 触发器: **每日** → 时间: **15:00**
5. 操作: **启动程序**
   - 程序或脚本: `C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor\daily_scheduler.py`
   - 工作目录: `C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor`
6. 设置 → 勾选 **如果错过计划，请尽快运行任务**

### 测试定时任务

```powershell
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Test
```

### 查看任务状态

```powershell
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Status
```

### 删除定时任务（如需）

```powershell
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Delete
```

---

## 📊 工作流程示例

### 第 1 天（2026-03-18）下午 3:00

系统自动执行，你在飞书收到：

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

【跟踪项目更新】(0 项)
──────────────────────────────────
[当前无变化]

【监测完成】 新项目: 2 | 变化: 0
```

### 你的回复（仍在飞书中或直接命令）

```
我要监测第 1、2 项
```

你确认要监测的项目后，系统添加到跟踪列表。

### 第 3 天（2026-03-20）下午 3:00

系统再次执行，这次能检测变化：

```
【每日中山平台监测报告】
发送时间: 2026-03-20 15:00:00

【新项目】(1 个)
──────────────────────────────────
[1] 中心四路项目
    栏目: 道路
    发布: 2026-03-20 10:30:00
    URL: https://...

【跟踪项目更新】(2 项)
──────────────────────────────────
[proj_001] 医药城项目
  * 发布澄清: 投资额调整为 5 亿元
  * 新增答疑: 关于供应商选择的问题

[proj_002] 翠锦路项目
  * 发布澄清: 施工进度调整说明
  * 更新时间: 2026-03-20 10:00:00

【监测完成】 新项目: 1 | 变化: 2
```

---

## 🛠️ 故障排除

### 问题 1: "Python 未找到" 或 "脚本不能执行"

**原因**: Python 环境未配置或路径有问题

**解决方案**:
1. 打开 PowerShell，确认 Python 可用：
   ```powershell
   python --version
   ```
2. 如果显示版本，则 Python 正常。否则需要安装或添加到 PATH

### 问题 2: 飞书消息发送失败

**原因**: Webhook URL 配置错误或网络连接问题

**解决方案**:
1. 检查配置：
   ```bash
   type config\feishu.json
   ```
2. 重新配置 Webhook URL：
   ```bash
   python scripts/feishu_sender.py --setup "新的 Webhook URL"
   ```
3. 测试连接：
   ```bash
   python scripts/feishu_sender.py --test
   ```

### 问题 3: 定时任务没有在规定时间运行

**原因**: 系统休眠、权限问题或任务配置错误

**解决方案**:
1. 检查任务是否已创建：
   ```powershell
   Get-ScheduledTask -TaskName "中山平台每日监测"
   ```
2. 检查任务历史：
   - 打开 **事件查看器** → **Windows 日志** → **系统**
   - 搜索 "TaskScheduler" 相关错误
3. 确保系统不在定时任务运行时休眠

### 问题 4: 监测脚本执行出错

**解决方案**:
1. 手动运行脚本查看错误：
   ```bash
   cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
   python daily_scheduler.py
   ```
2. 检查网络连接是否正常
3. 查看 `config/` 目录中的配置文件是否完整

---

## 📈 监控和维护

### 查看最近的监测结果

```bash
cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
# 查看最新的检查数据
type memory\last-check.json
```

### 查看跟踪的项目

```bash
# 显示当前跟踪列表
python tracking.py --show
```

### 添加/移除要监测的项目

```bash
# 添加项目
python tracking.py --add 1 2 3

# 移除项目
python tracking.py --remove proj_001
```

### 手动运行一次监测

```bash
# 立即执行监测（不等待定时）
python daily_scheduler.py
```

---

## 🔄 高级配置

### 修改执行时间

如果想改成其他时间（例如每天早上 9 点）：

**Windows 任务计划程序方式**:
1. 打开 **任务计划程序**
2. 找到 **中山平台每日监测**
3. 右键 → **编辑** → **触发器** → 修改时间为 **09:00**

**PowerShell 方式**:
```powershell
# 删除并重新创建
powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Delete

# 编辑 setup_scheduler.ps1，修改这一行：
# 从: -At 15:00
# 改为: -At 09:00

powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1 -Create
```

### 添加额外的通知渠道

编辑 `daily_scheduler.py`，添加更多通知方式：

```python
# 发送到邮件
email_sender.send_report(new_projects, tracked_changes)

# 保存到本地文件
save_to_file(new_projects, tracked_changes)

# 发送到钉钉
dingtalk_sender.send_report(new_projects, tracked_changes)
```

---

## 📝 完整设置清单

使用此清单追踪你的设置进度：

- [ ] 已获取飞书 Webhook URL
- [ ] 已配置 Webhook URL: `python scripts/feishu_sender.py --setup "..."`
- [ ] 已测试飞书消息: `python scripts/feishu_sender.py --test`
- [ ] 已创建 Windows 定时任务或 WorkBuddy 自动化
- [ ] 已手动测试监测脚本: `python daily_scheduler.py`
- [ ] 已确认定时任务在 15:00 运行
- [ ] 已添加要监测的项目到跟踪列表
- [ ] 系统运行正常，已收到飞书通知

---

## 📞 需要帮助？

如果遇到问题，可以：

1. **查看日志**:
   ```bash
   cd C:\Users\Administrator\.workbuddy\skills\zhongshan-monitor
   # 查看最近的监测日志
   ls -la memory/
   ```

2. **手动运行测试**:
   ```bash
   python daily_scheduler.py
   ```

3. **检查配置**:
   ```bash
   cat config/feishu.json
   ```

4. **查看文档**:
   - `DAILY_AUTOMATION_SETUP.md` - 自动化设置详情
   - `TRACKING_GUIDE.md` - 使用指南
   - `PROJECT_TRACKING_SYSTEM.md` - 系统架构

---

**系统已完全准备就绪！只需完成上述设置步骤即可开始使用。** 🎉
