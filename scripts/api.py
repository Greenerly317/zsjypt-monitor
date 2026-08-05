#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目跟踪系统 - 通用 API 接口
提供给外部应用（Webhook、OpenClaw、飞书、钉钉等）调用的 API
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# 修复 Windows 编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from monitor import ZhongshanMonitor
from tracking_manager import TrackingManager

class TrackingAPI:
    """项目跟踪 API 接口"""
    
    def __init__(self):
        self.monitor = ZhongshanMonitor('API')
        self.manager = TrackingManager()
    
    # ==================== 查询类 API ====================
    
    def get_daily_report(self) -> Dict[str, Any]:
        """
        获取每日新项目报告
        
        Returns:
            {
                "status": "success" | "error",
                "data": {
                    "new_projects": [
                        {
                            "index": 1,
                            "title": "项目名",
                            "category": "栏目",
                            "url": "URL",
                            "publish_time": "时间",
                        },
                        ...
                    ],
                    "timestamp": "2026-03-18 10:00:00"
                },
                "message": "发现 2 个新项目"
            }
        """
        try:
            projects = self.monitor.fetch_platform_projects()
            if not projects:
                return {
                    "status": "success",
                    "data": {"new_projects": [], "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                    "message": "无新项目"
                }
            
            last_check = self.monitor.load_last_check()
            new_projects = self.monitor.detect_new_projects(projects, last_check)
            
            # 格式化输出
            formatted = []
            for i, proj in enumerate(new_projects, 1):
                formatted.append({
                    "index": i,
                    "title": proj.get("title", ""),
                    "category": proj.get("category", ""),
                    "url": proj.get("url", ""),
                    "publish_time": proj.get("publish_time", ""),
                })
            
            # 保存检查点
            self.monitor.save_check_result(projects)
            
            return {
                "status": "success",
                "data": {
                    "new_projects": formatted,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "count": len(formatted)
                },
                "message": "发现 %d 个新项目" % len(formatted)
            }
        except Exception as e:
            return {
                "status": "error",
                "data": None,
                "message": "获取新项目失败: %s" % str(e)
            }
    
    def get_tracked_projects(self) -> Dict[str, Any]:
        """
        获取当前跟踪的项目列表
        
        Returns:
            {
                "status": "success",
                "data": {
                    "projects": [
                        {
                            "id": "proj_001",
                            "title": "项目名",
                            "category": "栏目",
                            "status": "跟踪中",
                            "added_date": "2026-03-18 10:00:00",
                            "last_update": "2026-03-18 12:30:00",
                        },
                        ...
                    ],
                    "count": 2
                }
            }
        """
        try:
            tracked = self.manager.get_tracked_projects()
            
            formatted = []
            for pid, proj in tracked.items():
                formatted.append({
                    "id": pid,
                    "title": proj.get("title", ""),
                    "category": proj.get("category", ""),
                    "url": proj.get("url", ""),
                    "status": proj.get("status", ""),
                    "added_date": proj.get("added_date", ""),
                    "last_update": proj.get("last_update", ""),
                })
            
            return {
                "status": "success",
                "data": {
                    "projects": formatted,
                    "count": len(formatted)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "data": None,
                "message": "获取跟踪项目失败: %s" % str(e)
            }
    
    def get_project_timeline(self, project_id: str) -> Dict[str, Any]:
        """
        获取某个项目的完整变化时间线
        
        Args:
            project_id: 项目 ID (如 proj_001)
            
        Returns:
            {
                "status": "success",
                "data": {
                    "project": {
                        "id": "proj_001",
                        "title": "项目名",
                        ...
                    },
                    "timeline": [
                        {
                            "event_type": "新增澄清",
                            "detail": "发布了 1 条澄清",
                            "timestamp": "2026-03-21 10:15:30"
                        },
                        ...
                    ]
                }
            }
        """
        try:
            if project_id not in self.manager.tracked_projects:
                return {
                    "status": "error",
                    "message": "项目不存在: %s" % project_id
                }
            
            proj_info = self.manager.tracked_projects[project_id]
            timeline = self.manager.get_project_timeline(project_id)
            
            return {
                "status": "success",
                "data": {
                    "project": {
                        "id": project_id,
                        "title": proj_info.get("title", ""),
                        "category": proj_info.get("category", ""),
                        "status": proj_info.get("status", ""),
                        "added_date": proj_info.get("added_date", ""),
                        "last_update": proj_info.get("last_update", ""),
                    },
                    "timeline": timeline
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "获取时间线失败: %s" % str(e)
            }
    
    def check_project_changes(self) -> Dict[str, Any]:
        """
        检查所有跟踪项目的变化
        
        Returns:
            {
                "status": "success",
                "data": {
                    "changes_detected": [
                        {
                            "project_id": "proj_001",
                            "project_title": "翠锦路项目",
                            "changes": [
                                {
                                    "type": "新增澄清",
                                    "detail": "发布了 1 条澄清"
                                },
                                ...
                            ]
                        },
                        ...
                    ],
                    "has_changes": true,
                    "timestamp": "2026-03-21 10:30:00"
                },
                "message": "发现 2 个项目有变化"
            }
        """
        try:
            tracked = self.manager.get_tracked_projects()
            
            if not tracked:
                return {
                    "status": "success",
                    "data": {
                        "changes_detected": [],
                        "has_changes": False,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "message": "没有在跟踪的项目"
                }
            
            all_projects = self.monitor.fetch_platform_projects()
            project_map = {proj.get("url"): proj for proj in all_projects}
            
            changes_detected = []
            
            for pid, proj_info in tracked.items():
                project_url = proj_info.get("url")
                
                if project_url not in project_map:
                    continue
                
                current_data = project_map[project_url]
                has_change, changes = self.manager.update_project_data(pid, current_data)
                
                if has_change:
                    changes_detected.append({
                        "project_id": pid,
                        "project_title": proj_info.get("title", ""),
                        "changes": [
                            {"type": ct, "detail": cd}
                            for ct, cd in changes
                        ]
                    })
            
            return {
                "status": "success",
                "data": {
                    "changes_detected": changes_detected,
                    "has_changes": len(changes_detected) > 0,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "message": "发现 %d 个项目有变化" % len(changes_detected) if changes_detected else "所有项目无新变化"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "检查变化失败: %s" % str(e)
            }
    
    # ==================== 操作类 API ====================
    
    def add_projects_to_tracking(self, project_indices: List[int]) -> Dict[str, Any]:
        """
        添加项目到跟踪列表
        
        Args:
            project_indices: 项目索引列表，如 [1, 2, 3]
            
        Returns:
            {
                "status": "success",
                "data": {
                    "added_count": 2,
                    "added_projects": [
                        {
                            "id": "proj_001",
                            "title": "项目名"
                        },
                        ...
                    ]
                },
                "message": "成功添加 2 个项目"
            }
        """
        try:
            projects = self.monitor.fetch_platform_projects()
            last_check = self.monitor.load_last_check()
            new_projects = self.monitor.detect_new_projects(projects, last_check)
            
            added_projects = []
            for idx in project_indices:
                if 1 <= idx <= len(new_projects):
                    proj = new_projects[idx - 1]
                    pid = self.manager.add_tracked_project(proj)
                    added_projects.append({
                        "id": pid,
                        "title": proj.get("title", "")
                    })
            
            return {
                "status": "success" if added_projects else "warning",
                "data": {
                    "added_count": len(added_projects),
                    "added_projects": added_projects
                },
                "message": "成功添加 %d 个项目" % len(added_projects)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "添加项目失败: %s" % str(e)
            }
    
    def remove_project_from_tracking(self, project_id: str) -> Dict[str, Any]:
        """
        移除项目的跟踪
        
        Args:
            project_id: 项目 ID (如 proj_001)
            
        Returns:
            {
                "status": "success",
                "message": "已移除: 翠锦路项目"
            }
        """
        try:
            if project_id not in self.manager.tracked_projects:
                return {
                    "status": "error",
                    "message": "项目不存在: %s" % project_id
                }
            
            title = self.manager.tracked_projects[project_id].get("title", "")
            self.manager.remove_tracked_project(project_id)
            
            return {
                "status": "success",
                "message": "已移除: %s" % title
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "移除项目失败: %s" % str(e)
            }
    
    # ==================== 导出类 API ====================
    
    def export_tracking_data(self) -> Dict[str, Any]:
        """
        导出所有跟踪数据（用于备份或迁移）
        
        Returns:
            {
                "status": "success",
                "data": {
                    "tracked_projects": {...},
                    "history": [...],
                    "export_time": "2026-03-18 10:00:00"
                }
            }
        """
        try:
            return {
                "status": "success",
                "data": {
                    "tracked_projects": self.manager.tracked_projects,
                    "history": self.manager.history,
                    "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "导出数据失败: %s" % str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计数据
        
        Returns:
            {
                "status": "success",
                "data": {
                    "total_tracked": 5,           # 总跟踪项目数
                    "recent_changes": 3,         # 最近 24 小时的变化数
                    "avg_change_per_day": 1.2,   # 平均每天变化数
                    "most_active_project": "proj_001"
                }
            }
        """
        try:
            tracked = self.manager.get_tracked_projects()
            recent = self.manager.get_recent_changes(hours=24)
            
            # 统计每个项目的变化次数
            project_changes = {}
            for event in self.manager.history:
                pid = event.get("project_id")
                project_changes[pid] = project_changes.get(pid, 0) + 1
            
            most_active = max(project_changes, key=project_changes.get) if project_changes else None
            
            return {
                "status": "success",
                "data": {
                    "total_tracked": len(tracked),
                    "recent_changes_24h": len(recent),
                    "total_events": len(self.manager.history),
                    "most_active_project": most_active,
                    "projects_with_changes": len([p for p in project_changes.values() if p > 0])
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "获取统计失败: %s" % str(e)
            }


# ==================== 独立函数接口 ====================

def call_api(method: str, **kwargs) -> str:
    """
    通用 API 调用接口
    
    Usage:
        result = call_api("get_daily_report")
        result = call_api("add_projects_to_tracking", project_indices=[1, 2])
        
    Returns:
        JSON 字符串
    """
    api = TrackingAPI()
    
    try:
        if method == "get_daily_report":
            result = api.get_daily_report()
        elif method == "get_tracked_projects":
            result = api.get_tracked_projects()
        elif method == "get_project_timeline":
            result = api.get_project_timeline(kwargs.get("project_id", ""))
        elif method == "check_project_changes":
            result = api.check_project_changes()
        elif method == "add_projects_to_tracking":
            result = api.add_projects_to_tracking(kwargs.get("project_indices", []))
        elif method == "remove_project_from_tracking":
            result = api.remove_project_from_tracking(kwargs.get("project_id", ""))
        elif method == "export_tracking_data":
            result = api.export_tracking_data()
        elif method == "get_statistics":
            result = api.get_statistics()
        else:
            result = {
                "status": "error",
                "message": "未知的 API 方法: %s" % method
            }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": "API 调用异常: %s" % str(e)
        }, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # 命令行测试
    import sys
    
    if len(sys.argv) > 1:
        method = sys.argv[1]
        # 解析额外参数
        kwargs = {}
        for i in range(2, len(sys.argv), 2):
            if i + 1 < len(sys.argv):
                key = sys.argv[i].lstrip('--')
                value = sys.argv[i + 1]
                # 尝试解析为 JSON
                try:
                    kwargs[key] = json.loads(value)
                except:
                    kwargs[key] = value
        
        print(call_api(method, **kwargs))
    else:
        print("用法:")
        print("  python api.py get_daily_report")
        print("  python api.py get_tracked_projects")
        print("  python api.py check_project_changes")
        print("  python api.py add_projects_to_tracking --project_indices '[1,2,3]'")
        print("  python api.py remove_project_from_tracking --project_id 'proj_001'")
        print("  python api.py export_tracking_data")
        print("  python api.py get_statistics")
