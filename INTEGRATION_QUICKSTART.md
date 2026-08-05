# 项目跟踪系统 - 集成应用总结

## 📌 快速导航

| 文档 | 适用场景 |
|------|--------|
| [TRACKING_GUIDE.md](./TRACKING_GUIDE.md) | 👤 **个人使用** - 如何使用每日汇报、项目管理 |
| [PROJECT_TRACKING_SYSTEM.md](../brain/PROJECT_TRACKING_SYSTEM.md) | 📊 **系统设计** - 完整工作流程和架构 |
| [OPENCLAW_INTEGRATION.md](./OPENCLAW_INTEGRATION.md) | 🤖 **OpenClaw** - 如何集成到 OpenClaw Agent |
| [INTEGRATION_MANUAL.md](../brain/INTEGRATION_MANUAL.md) | 🔌 **应用集成** - 集成到各类应用 |
| **本文档** | 📋 **快速参考** - API 总览和集成示例 |

---

## 🎯 核心功能

这套系统提供了**8 个核心 API 方法**，可以完全满足所有监测需求：

```python
from scripts.api import TrackingAPI

api = TrackingAPI()

# 1. 获取每日新项目
daily_report = api.get_daily_report()

# 2. 获取跟踪列表
tracked = api.get_tracked_projects()

# 3. 检查项目变化
changes = api.check_project_changes()

# 4. 获取项目时间线
timeline = api.get_project_timeline('proj_001')

# 5. 添加项目到跟踪
result = api.add_projects_to_tracking([1, 2, 3])

# 6. 移除项目跟踪
result = api.remove_project_from_tracking('proj_001')

# 7. 导出数据
data = api.export_tracking_data()

# 8. 获取统计数据
stats = api.get_statistics()
```

---

## 🚀 最快开始（3 种方式）

### 方式 1️⃣ : Python 直接调用

```python
# 最简单的方式，3 行代码
from scripts.api import TrackingAPI

api = TrackingAPI()
report = api.get_daily_report()
print(report)
```

### 方式 2️⃣ : 命令行调用

```bash
# 最快的方式，1 行命令
python scripts/api.py get_daily_report
python scripts/api.py check_project_changes
python scripts/api.py get_tracked_projects
```

### 方式 3️⃣ : HTTP API 服务

```python
# 最灵活的方式，适合分布式
# 启动服务器
python scripts/api_server.py

# 调用 API
curl http://localhost:5000/tracking/daily-report
```

---

## 📂 文件结构

```
zhongshan-monitor/
├── scripts/
│   ├── api.py                 # ⭐ 核心 API 接口
│   ├── monitor.py             # 平台监控器
│   ├── tracking_manager.py    # 项目跟踪管理器
│   └── ...
│
├── daily_report.py            # 每日汇报脚本
├── tracking.py                # 项目确认脚本
├── track_changes.py           # 变化监测脚本
├── demo.py                    # 演示脚本
├── openclaw_agent.py          # OpenClaw 代理
│
└── 文档/
    ├── TRACKING_GUIDE.md                # 完整使用指南
    ├── OPENCLAW_INTEGRATION.md          # OpenClaw 集成
    └── ...
```

---

## 💻 常见集成场景

### 场景 1: OpenClaw 内部集成

```python
# 在 OpenClaw Agent 中添加这段代码
from scripts.api import TrackingAPI

api = TrackingAPI()

# 根据用户请求调用 API
if "新项目" in user_input:
    result = api.get_daily_report()
elif "变化" in user_input:
    result = api.check_project_changes()
elif "监测" in user_input:
    indices = extract_indices(user_input)  # 提取数字
    result = api.add_projects_to_tracking(indices)

# 返回结果
return format_response(result)
```

**使用效果**:
```
用户: 有什么新项目吗？
Agent: [调用 get_daily_report()] → 返回新项目清单

用户: 我要监测第 2、3 项目
Agent: [调用 add_projects_to_tracking([2,3])] → 确认添加

用户: 有什么变化吗？
Agent: [调用 check_project_changes()] → 返回变化列表
```

### 场景 2: 飞书机器人集成

```python
import requests
from scripts.api import TrackingAPI

api = TrackingAPI()

# 每天早上 8:00 发送新项目报告
report = api.get_daily_report()

if report["data"]["new_projects"]:
    message = "【新项目报告】\n"
    for proj in report["data"]["new_projects"]:
        message += f"[{proj['index']}] {proj['title']}\n"
    
    # 发送到飞书
    requests.post(FEISHU_WEBHOOK, json={
        "msg_type": "text",
        "content": {"text": message}
    })
```

### 场景 3: Web Dashboard

```python
from flask import Flask, jsonify
from scripts.api import TrackingAPI

app = Flask(__name__)
api = TrackingAPI()

@app.route('/dashboard')
def dashboard():
    """完整的项目监测 Dashboard"""
    return jsonify({
        "tracked_projects": api.get_tracked_projects(),
        "recent_changes": api.check_project_changes(),
        "statistics": api.get_statistics()
    })

if __name__ == '__main__':
    app.run()
```

### 场景 4: 定时自动化

```python
import schedule
from scripts.api import TrackingAPI

api = TrackingAPI()

# 每天 8:00 检查新项目
schedule.every().day.at("08:00").do(
    lambda: notify_user(api.get_daily_report())
)

# 每天 12:00、16:00、20:00 检查变化
for hour in [12, 16, 20]:
    schedule.every().day.at(f"{hour}:00").do(
        lambda: alert_user(api.check_project_changes())
    )

schedule.run_all()
```

---

## 📊 API 返回格式

所有 API 都返回统一格式的 JSON：

### 成功响应
```json
{
  "status": "success",
  "data": {
    "项目": "数据",
    "timestamp": "2026-03-18 10:00:00"
  },
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "status": "error",
  "data": null,
  "message": "错误原因"
}
```

---

## 🔄 完整工作流程

```
[日报汇报]
    ↓ api.get_daily_report()
    ↓ 返回新项目清单
    ↓
[用户确认]
    ↓ 告诉我要监测的项目
    ↓
[添加到跟踪]
    ↓ api.add_projects_to_tracking([1,2,3])
    ↓ 建立项目档案
    ↓
[定期监测]
    ↓ api.check_project_changes() (每天 3 次)
    ↓ 检测是否有澄清、答疑、附件等更新
    ↓
[发现变化]
    ↓ 立即通知用户
    ↓ 记录到项目时间线
    ↓
[查询历史]
    ↓ api.get_project_timeline('proj_001')
    ↓ 显示完整的项目变化历史
    ↓
[项目结束]
    ↓ api.remove_project_from_tracking('proj_001')
    ↓ 移除监测
```

---

## 📋 文件清单

| 文件 | 说明 | 用途 |
|------|------|------|
| `scripts/api.py` | ⭐ 核心 API 接口 | 所有集成的基础 |
| `daily_report.py` | 每日汇报脚本 | 生成新项目清单 |
| `tracking.py` | 项目确认脚本 | 添加/移除项目 |
| `track_changes.py` | 变化监测脚本 | 检查项目更新 |
| `demo.py` | 演示脚本 | 快速测试 API |
| `openclaw_agent.py` | OpenClaw 代理 | 集成到 OpenClaw |
| `TRACKING_GUIDE.md` | 使用指南 | 个人用户 |
| `OPENCLAW_INTEGRATION.md` | OpenClaw 集成 | OpenClaw 用户 |
| `INTEGRATION_MANUAL.md` | 应用集成手册 | 开发者 |

---

## 🎯 使用建议

### 对于个人用户

```bash
# 每天 8:00 运行
python daily_report.py

# 根据汇报，告诉我要监测的项目
# "我要监测第 2、3 项目"

# 每天定时运行（建议 3 次：12:00、16:00、20:00）
python track_changes.py
```

### 对于 OpenClaw 用户

在 OpenClaw Agent 中添加：

```python
from scripts.api import TrackingAPI

api = TrackingAPI()

# 监听用户的自然语言请求
# 自动调用对应的 API
```

### 对于开发者

集成 API 到你的应用：

```python
# 导入 API
from zhongshan_monitor.scripts.api import TrackingAPI

# 初始化
api = TrackingAPI()

# 使用任意方法
result = api.get_daily_report()

# 处理结果
if result["status"] == "success":
    # 你的逻辑
    pass
```

---

## ⚡ 快速参考

### 获取新项目
```python
api.get_daily_report()
```

### 显示监测列表
```python
api.get_tracked_projects()
```

### 检查项目变化
```python
api.check_project_changes()
```

### 查看项目历史
```python
api.get_project_timeline('proj_001')
```

### 添加项目
```python
api.add_projects_to_tracking([1, 2, 3])
```

### 移除项目
```python
api.remove_project_from_tracking('proj_001')
```

### 导出数据
```python
api.export_tracking_data()
```

### 查看统计
```python
api.get_statistics()
```

---

## 🔗 相关资源

- **完整指南**: TRACKING_GUIDE.md
- **系统设计**: PROJECT_TRACKING_SYSTEM.md
- **OpenClaw 集成**: OPENCLAW_INTEGRATION.md
- **应用集成**: INTEGRATION_MANUAL.md
- **API 代码**: scripts/api.py
- **演示脚本**: demo.py

---

## ✅ 验证

所有功能已测试完全可用：

✅ API 接口正常  
✅ 日报汇报正常  
✅ 项目追踪正常  
✅ 变化监测正常  
✅ 数据持久化正常  
✅ 编码兼容性正常  

---

## 🎉 总结

这套系统提供了：

1. **开放的 API** - 可以集成到任何应用
2. **多种调用方式** - Python、命令行、HTTP
3. **完整的文档** - 使用指南和集成手册
4. **生产就绪** - 经过充分测试
5. **易于扩展** - 模块化设计

**立即开始使用**: `python demo.py`

