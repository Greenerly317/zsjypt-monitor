# 🎯 中山资源交易平台监控 Skill - 使用导航

## 👋 欢迎！

你现在拥有一个**完整的、可用的中山资源交易平台监控 Skill**。

这个 Skill 可以：
- ✅ 每天自动监控平台新项目（3次/天：8:30、12:00、20:30）
- ✅ 自动识别"勘察""设计"相关项目
- ✅ 通过飞书立即通知你
- ✅ 保存完整的检查历史

---

## 🚀 立即开始（3步，5分钟）

### 第1步：初始化（自动配置）

打开命令行，运行：
```bash
python ~/.workbuddy/skills/zhongshan-monitor/init.py
```

这会自动：
- ✅ 检查文件是否完整
- ✅ 创建必要的目录
- ✅ 配置飞书通知
- ✅ 测试监控功能

### 第2步：配置飞书（2分钟）

脚本会提示你输入**飞书 Webhook URL**：

**如何获取?**
1. 打开飞书
2. 进入你想接收通知的群聊
3. 群聊设置 → 群机器人 → 添加机器人
4. 选择"自定义机器人" → 复制 Webhook URL

### 第3步：验证

运行测试：
```bash
python ~/.workbuddy/skills/zhongshan-monitor/run.py --shift 早班 --notify
```

如果成功，你会在飞书群里收到一条测试消息 ✅

---

## 📖 文档导航

| 文档 | 用途 | 何时阅读 |
|------|------|---------|
| **QUICKSTART.md** | 5分钟快速开始 | ⭐ **现在就读** |
| README.md | 完整功能说明 | 深入了解时 |
| STRUCTURE.md | 项目架构 | 需要自定义时 |
| CHECKLIST.md | 交付清单 | 了解所有功能 |

**推荐阅读顺序**:
```
QUICKSTART.md → README.md → STRUCTURE.md
```

---

## 🎮 日常使用

### 方式1：自动执行（推荐）

配置完成后，系统会自动执行：
- 🌅 **08:30** - 早班检查
- ☀️ **12:00** - 午班检查  
- 🌆 **20:30** - 晚班检查

你只需等待飞书通知即可。

### 方式2：手动执行

想立即检查？运行：
```bash
# 不发送通知（仅查看结果）
python ~/.workbuddy/skills/zhongshan-monitor/run.py --shift 早班

# 发送飞书通知
python ~/.workbuddy/skills/zhongshan-monitor/run.py --shift 早班 --notify
```

### 方式3：查看历史

```bash
# 查看最新检查结果
cat ~/.workbuddy/skills/zhongshan-monitor/memory/last-check.json

# 查看所有历史记录
ls ~/.workbuddy/skills/zhongshan-monitor/memory/archive/

# 查看执行日志
tail ~/.workbuddy/skills/zhongshan-monitor/logs/monitor_*.log
```

---

## ❓ 常见问题

### Q: 如何修改监控时间？
A: 在 WorkBuddy IDE 中编辑定时任务，修改执行时间即可

### Q: 如何添加其他关键词？
A: 编辑 `config/platform-config.json`
```json
"keywords": ["勘察", "设计", "勘察设计", "你的新关键词"]
```

### Q: 如何只监控某个分类？
A: 编辑 `config/platform-config.json`
```json
"categories": ["建设工程"]  // 或 ["政府采购"]
```

### Q: 飞书没有收到通知？
A: 
1. 检查 Webhook URL 是否正确
2. 检查飞书机器人是否在群聊中
3. 运行 `python init.py` 重新配置

### Q: 如何禁用某个班次？
A: 在 WorkBuddy 中禁用对应的定时任务

---

## 📁 文件结构一览

```
~/.workbuddy/skills/zhongshan-monitor/
├── QUICKSTART.md ⭐ 从这里开始
├── README.md (完整指南)
├── STRUCTURE.md (项目架构)
├── CHECKLIST.md (交付清单)
├── init.py (一键初始化)
├── run.py (启动脚本)
├── scripts/ (核心代码)
├── config/ (配置文件)
├── memory/ (数据存储，自动创建)
└── logs/ (日志文件，自动创建)
```

---

## 🔧 故障排查

### 问题：运行脚本时出错

**解决方案**：
```bash
# 1. 检查 Python 版本
python --version  # 需要 3.7+

# 2. 重新初始化
python ~/.workbuddy/skills/zhongshan-monitor/init.py

# 3. 查看日志
tail ~/.workbuddy/skills/zhongshan-monitor/logs/*.log
```

### 问题：飞书通知发送失败

**解决方案**：
```bash
# 1. 重新配置飞书
python ~/.workbuddy/skills/zhongshan-monitor/run.py --setup-feishu

# 2. 测试通知
python ~/.workbuddy/skills/zhongshan-monitor/run.py --shift 早班 --notify

# 3. 检查配置
cat ~/.workbuddy/skills/zhongshan-monitor/config/feishu.json
```

### 问题：定时任务未执行

**解决方案**：
1. 检查 WorkBuddy 后台是否运行
2. 验证定时任务是否启用（在 IDE 中检查）
3. 检查系统时间是否准确
4. 查看日志了解执行情况

---

## ✨ 功能一览

| 功能 | 说明 |
|------|------|
| 🌐 平台监控 | 实时访问中山资源交易平台 |
| 🔍 关键词筛选 | 自动识别"勘察""设计"等项目 |
| ➕ 增量检测 | 对比历史记录，只通知新项目 |
| 📱 飞书通知 | 发现新项目立即推送飞书 |
| ⏰ 三班制 | 每天自动执行三次（8:30/12:00/20:30） |
| 📊 历史记录 | 完整保存所有检查结果 |
| 📝 日志记录 | 详细的执行日志便于调试 |
| ⚙️ 灵活配置 | 支持自定义关键词、时间、分类 |

---

## 🎯 使用流程

```
┌─────────────────────────────────────────────┐
│ 运行 init.py 进行一键初始化                    │
│ (检查、创建目录、配置飞书、测试)               │
└────────────┬────────────────────────────────┘
             │
             ✅ 初始化完成
             │
┌────────────▼────────────────────────────────┐
│ 定时任务自动执行                              │
│ (8:30 早班 / 12:00 午班 / 20:30 晚班)        │
└────────────┬────────────────────────────────┘
             │
        ┌────▼─────────────────────┐
        │                          │
    无新项目                   有新项目
        │                          │
        ✅ 默认不通知        │
        │                   ✅ 发送飞书通知
        │                   │
        └───────────┬───────┘
                    │
            飞书群里收到通知
            (项目名、类型、链接等)
```

---

## 💡 最佳实践

1. **首次使用**
   - 运行 `init.py` 完成初始化
   - 在合适的飞书群配置机器人
   - 测试验证功能正常

2. **日常使用**
   - 无需手动操作，系统自动监控
   - 定期检查飞书通知
   - 如需调整，编辑配置文件

3. **定期维护**
   - 每月检查 `memory/archive/` 大小
   - 如需要可清理过期文件
   - 检查 `logs/` 是否有异常

4. **自定义**
   - 修改关键词：编辑 `config/platform-config.json`
   - 修改分类：编辑 `scripts/monitor.py`
   - 修改时间：在 WorkBuddy IDE 中编辑定时任务

---

## 📞 需要帮助？

### 快速参考

- 📖 **快速开始**: 阅读 QUICKSTART.md
- 📚 **完整文档**: 阅读 README.md
- 🔧 **架构说明**: 阅读 STRUCTURE.md
- 📋 **交付清单**: 阅读 CHECKLIST.md

### 常见命令

```bash
# 初始化
python ~/.workbuddy/skills/zhongshan-monitor/init.py

# 配置飞书
python ~/.workbuddy/skills/zhongshan-monitor/run.py --setup-feishu

# 手动执行
python ~/.workbuddy/skills/zhongshan-monitor/run.py --shift 早班 --notify

# 查看结果
cat ~/.workbuddy/skills/zhongshan-monitor/memory/last-check.json

# 查看日志
tail ~/.workbuddy/skills/zhongshan-monitor/logs/*.log
```

---

## ✅ 准备就绪！

你已经拥有一个**完整的、可用的监控系统**。

**下一步**：
```bash
python ~/.workbuddy/skills/zhongshan-monitor/init.py
```

祝你使用愉快！🚀

---

**最后更新**: 2026-03-17
**版本**: v1.0
**状态**: ✅ 生产就绪
