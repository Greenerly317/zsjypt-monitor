# OpenClaw 集成方案

## 快速开始

在 OpenClaw 中集成中山平台项目跟踪系统只需 3 步：

### 1️⃣ 配置 OpenClaw Agent

在你的 OpenClaw 配置中添加这个 Agent：

```yaml
agent:
  name: "zhongshan-monitor"
  description: "中山资源交易平台项目跟踪"
  triggers:
    - pattern: "监测|跟踪|项目"
    - schedule: "0 8 * * *"  # 每天 8:00
  actions:
    - get_daily_report
    - check_project_changes
```

### 2️⃣ 集成点

#### 定时检测新项目

```python
# 在 OpenClaw 的定时任务中调用
from scripts.api import TrackingAPI

api = TrackingAPI()

# 每天早上 8:00 执行
report = api.get_daily_report()

if report["data"]["new_projects"]:
    # 发送通知
    send_notification({
        "title": report["message"],
        "content": format_projects(report["data"]["new_projects"])
    })
```

#### 定时监测变化

```python
# 每天 12:00、16:00、20:00 执行
changes = api.check_project_changes()

if changes["data"]["has_changes"]:
    # 发送告警通知
    send_alert({
        "title": "项目有更新",
        "projects": changes["data"]["changes_detected"]
    })
```

#### 提供 Web Dashboard

```python
# 在 OpenClaw 中提供 API 接口
from flask import Flask, jsonify
from scripts.api import TrackingAPI

app = Flask(__name__)
api = TrackingAPI()

@app.route('/api/dashboard')
def dashboard():
    """项目跟踪 Dashboard"""
    return jsonify({
        "tracked": api.get_tracked_projects(),
        "statistics": api.get_statistics(),
        "recent_changes": api.check_project_changes()
    })

@app.route('/api/project/<project_id>/timeline')
def project_timeline(project_id):
    """项目时间线"""
    return jsonify(api.get_project_timeline(project_id))
```

---

## 详细集成指南

### 方案 A: 直接 Python 调用

**最简单，推荐用于 OpenClaw 内部脚本**

```python
import sys
sys.path.insert(0, '/path/to/zhongshan-monitor/scripts')

from api import TrackingAPI

api = TrackingAPI()

# 获取新项目
daily_report = api.get_daily_report()
print(daily_report)

# 检查变化
changes = api.check_project_changes()
print(changes)

# 添加项目到跟踪
result = api.add_projects_to_tracking([1, 2, 3])
print(result)
```

### 方案 B: 命令行调用

**用于 Shell 脚本或系统命令**

```bash
# 获取每日报告
python ~/scripts/api.py get_daily_report

# 检查变化
python ~/scripts/api.py check_project_changes

# 添加项目到跟踪
python ~/scripts/api.py add_projects_to_tracking --project_indices '[1,2]'

# 导出数据
python ~/scripts/api.py export_tracking_data
```

### 方案 C: HTTP API 服务

**用于远程调用或跨应用通信**

```python
# 启动 API 服务器
from flask import Flask, request, jsonify
from scripts.api import TrackingAPI

app = Flask(__name__)
api = TrackingAPI()

@app.route('/tracking/daily-report', methods=['GET'])
def get_daily_report_api():
    """获取每日报告"""
    return jsonify(api.get_daily_report())

@app.route('/tracking/projects', methods=['GET'])
def get_projects_api():
    """获取跟踪项目列表"""
    return jsonify(api.get_tracked_projects())

@app.route('/tracking/changes', methods=['GET'])
def check_changes_api():
    """检查项目变化"""
    return jsonify(api.check_project_changes())

@app.route('/tracking/add', methods=['POST'])
def add_projects_api():
    """添加项目到跟踪"""
    data = request.json
    indices = data.get('project_indices', [])
    return jsonify(api.add_projects_to_tracking(indices))

@app.route('/tracking/remove/<project_id>', methods=['DELETE'])
def remove_project_api(project_id):
    """移除项目的跟踪"""
    return jsonify(api.remove_project_from_tracking(project_id))

@app.route('/tracking/statistics', methods=['GET'])
def get_statistics_api():
    """获取统计数据"""
    return jsonify(api.get_statistics())

if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=False)
```

**使用示例:**

```bash
# 获取每日报告
curl http://localhost:5000/tracking/daily-report

# 添加项目到跟踪
curl -X POST http://localhost:5000/tracking/add \
  -H "Content-Type: application/json" \
  -d '{"project_indices": [1, 2, 3]}'

# 检查变化
curl http://localhost:5000/tracking/changes
```

---

## OpenClaw 特定集成

### 1. 在 OpenClaw 中注册为 Tool

编辑 `.codebuddy/agents/tools/zhongshan-monitor.json`:

```json
{
  "name": "zhongshan_monitor",
  "description": "中山平台项目跟踪",
  "commands": [
    {
      "cmd": "daily_report",
      "description": "获取每日新项目报告",
      "impl": "python scripts/api.py get_daily_report"
    },
    {
      "cmd": "check_changes",
      "description": "检查项目变化",
      "impl": "python scripts/api.py check_project_changes"
    },
    {
      "cmd": "track_projects",
      "description": "添加项目到跟踪",
      "impl": "python scripts/api.py add_projects_to_tracking --project_indices %s"
    },
    {
      "cmd": "show_tracked",
      "description": "显示跟踪项目列表",
      "impl": "python scripts/api.py get_tracked_projects"
    }
  ]
}
```

### 2. 在 OpenClaw 中设置定时任务

编辑 `.codebuddy/automations/zhongshan-monitor.toml`:

```toml
[automation]
name = "中山平台日报"
description = "每天早上获取新项目报告"
prompt = "执行 zhongshan_monitor daily_report 并汇报结果"
rrule = "FREQ=DAILY;BYHOUR=8;BYMINUTE=0"
status = "ACTIVE"

[automation]
name = "中山平台变化监测"
description = "每天定时检查项目变化"
prompt = "执行 zhongshan_monitor check_changes 检查所有跟踪项目"
rrule = "FREQ=DAILY;BYHOUR=12,16,20;BYMINUTE=0"
status = "ACTIVE"
```

### 3. 在 OpenClaw Agent 中使用

在你的 OpenClaw Agent 配置中调用：

```python
# 在 Agent 的处理逻辑中
from claw.tools import execute_command

def handle_zhongshan_query(user_query):
    """处理中山平台相关查询"""
    
    if "新项目" in user_query:
        # 获取每日报告
        result = execute_command("python scripts/api.py get_daily_report")
        return f"【每日新项目】\n{result}"
    
    elif "监测" in user_query and "添加" in user_query:
        # 提取项目索引并添加
        indices = extract_indices(user_query)  # 实现这个函数
        result = execute_command(
            f"python scripts/api.py add_projects_to_tracking --project_indices {indices}"
        )
        return f"【项目已添加】\n{result}"
    
    elif "变化" in user_query:
        # 检查变化
        result = execute_command("python scripts/api.py check_project_changes")
        return f"【项目变化】\n{result}"
    
    elif "跟踪列表" in user_query or "监测列表" in user_query:
        # 显示跟踪列表
        result = execute_command("python scripts/api.py get_tracked_projects")
        return f"【当前跟踪列表】\n{result}"
    
    else:
        return "请告诉我你要做什么？"
```

---

## 其他应用集成示例

### 集成到飞书 / 钉钉

```python
# 飞书机器人集成
import requests
import json
from scripts.api import TrackingAPI

def send_feishu_message(webhook_url, message):
    """发送飞书消息"""
    data = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    requests.post(webhook_url, json=data)

api = TrackingAPI()

# 每天早上发送新项目报告
daily_report = api.get_daily_report()
if daily_report["data"]["new_projects"]:
    message = f"""【新项目报告】{daily_report['message']}

{format_projects_for_message(daily_report["data"]["new_projects"])}
"""
    send_feishu_message(FEISHU_WEBHOOK, message)
```

### 集成到 Django / Flask Web 应用

```python
# Django 视图
from django.http import JsonResponse
from django.views import View
from scripts.api import TrackingAPI

class TrackingDashboardView(View):
    """项目跟踪 Dashboard"""
    
    def get(self, request):
        api = TrackingAPI()
        return JsonResponse({
            "tracked_projects": api.get_tracked_projects(),
            "recent_changes": api.check_project_changes(),
            "statistics": api.get_statistics()
        })

class DailyReportView(View):
    """每日报告"""
    
    def get(self, request):
        api = TrackingAPI()
        return JsonResponse(api.get_daily_report())
```

### 集成到 Excel / CSV 导出

```python
import csv
import json
from scripts.api import TrackingAPI
from datetime import datetime

def export_tracking_to_csv():
    """导出跟踪数据到 CSV"""
    api = TrackingAPI()
    tracked = api.get_tracked_projects()
    
    filename = f"tracking_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['项目ID', '项目名', '栏目', '状态', '发布时间', '最后更新'])
        
        for proj in tracked["data"]["projects"]:
            writer.writerow([
                proj['id'],
                proj['title'],
                proj['category'],
                proj['status'],
                proj['added_date'],
                proj['last_update']
            ])
    
    return filename
```

---

## 最常用的集成方式

根据你的需求选择：

| 场景 | 推荐方案 |
|------|--------|
| OpenClaw 内部脚本 | **直接 Python 调用** |
| Shell 脚本 / Cron | **命令行调用** |
| 飞书 / 钉钉机器人 | **Python 调用 + Webhook** |
| Web Dashboard | **HTTP API 服务** |
| 跨应用通信 | **HTTP API** 或 **File Export** |
| 数据分析 | **导出为 JSON/CSV** |

---

## API 方法总览

| 方法 | 说明 | 返回 |
|------|------|------|
| `get_daily_report()` | 获取每日新项目 | 新项目列表 |
| `get_tracked_projects()` | 获取跟踪项目列表 | 项目列表 |
| `check_project_changes()` | 检查所有项目变化 | 变化列表 |
| `get_project_timeline(pid)` | 获取项目时间线 | 项目历史 |
| `add_projects_to_tracking(indices)` | 添加项目到跟踪 | 添加结果 |
| `remove_project_from_tracking(pid)` | 移除项目跟踪 | 操作结果 |
| `export_tracking_data()` | 导出所有数据 | 完整数据 |
| `get_statistics()` | 获取统计数据 | 统计信息 |

---

## 立即开始

### 最快的集成方式（3 行代码）

```python
from scripts.api import TrackingAPI

api = TrackingAPI()
report = api.get_daily_report()
print(report)  # 完成！
```

### 在 OpenClaw 中

```
@bot 检查一下中山平台有没有新项目
→ 执行 api.get_daily_report()
→ 返回新项目清单
```

完成！🎉
