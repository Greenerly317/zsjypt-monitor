#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目跟踪管理模块
负责管理需要持续监测的项目列表和变化检测
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set

class TrackingManager:
    """项目跟踪管理器"""
    
    def __init__(self):
        self.skill_dir = Path(__file__).parent.parent
        self.memory_dir = self.skill_dir / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 项目跟踪库文件
        self.tracking_file = self.memory_dir / "tracked_projects.json"
        # 项目变化历史记录
        self.history_file = self.memory_dir / "project_history.json"
        
        self.tracked_projects = self._load_tracked_projects()
        self.history = self._load_history()
    
    def _load_tracked_projects(self) -> Dict[str, Dict]:
        """加载已确认的跟踪项目列表"""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_tracked_projects(self):
        """保存跟踪项目列表"""
        with open(self.tracking_file, 'w', encoding='utf-8') as f:
            json.dump(self.tracked_projects, f, ensure_ascii=False, indent=2)
    
    def _load_history(self) -> List[Dict]:
        """加载项目变化历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """保存历史记录"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_tracked_project(self, project: Dict) -> str:
        """
        添加项目到跟踪列表
        
        Args:
            project: 项目信息 {title, category, url, publish_time, ...}
            
        Returns:
            项目 ID
        """
        project_id = f"proj_{len(self.tracked_projects) + 1:03d}"
        
        self.tracked_projects[project_id] = {
            "title": project.get("title", "未知"),
            "category": project.get("category", ""),
            "url": project.get("url", ""),
            "publish_time": project.get("publish_time", ""),
            "status": "跟踪中",
            "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "full_data": project,  # 保存完整数据
        }
        
        self._save_tracked_projects()
        
        # 记录添加事件
        self._record_event(project_id, "添加跟踪", f"项目已添加到跟踪列表")
        
        return project_id
    
    def remove_tracked_project(self, project_id: str):
        """移除跟踪项目"""
        if project_id in self.tracked_projects:
            title = self.tracked_projects[project_id].get("title", "")
            del self.tracked_projects[project_id]
            self._save_tracked_projects()
            self._record_event(project_id, "移除跟踪", f"项目已从跟踪列表移除")
    
    def get_tracked_projects(self) -> Dict[str, Dict]:
        """获取所有跟踪项目"""
        return self.tracked_projects
    
    def update_project_data(self, project_id: str, new_data: Dict):
        """
        更新项目数据并检测变化
        
        Args:
            project_id: 项目 ID
            new_data: 新的项目数据
            
        Returns:
            (是否有变化, 变化内容)
        """
        if project_id not in self.tracked_projects:
            return False, "项目不在跟踪列表中"
        
        old_data = self.tracked_projects[project_id].get("full_data", {})
        changes = self._detect_changes(old_data, new_data)
        
        if changes:
            print(f"[变化检测] {project_id}: 发现 {len(changes)} 项变化")
            
            # 更新项目数据
            self.tracked_projects[project_id].update({
                "full_data": new_data,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            self._save_tracked_projects()
            
            # 记录每项变化
            for change_type, change_detail in changes:
                self._record_event(project_id, change_type, change_detail)
            
            return True, changes
        
        return False, []
    
    def _detect_changes(self, old_data: Dict, new_data: Dict) -> List[tuple]:
        """
        检测项目数据的变化
        
        Returns:
            变化列表 [(change_type, detail), ...]
        """
        changes = []
        
        # 检测常见变化类型
        if new_data.get("status") != old_data.get("status"):
            changes.append(("状态更新", f"从 {old_data.get('status')} 变为 {new_data.get('status')}"))
        
        if new_data.get("content") and new_data.get("content") != old_data.get("content"):
            changes.append(("内容更新", "项目内容已更新"))
        
        # 检测是否新增了澄清、答疑、附件等
        old_clarifications = old_data.get("clarifications", [])
        new_clarifications = new_data.get("clarifications", [])
        if len(new_clarifications) > len(old_clarifications):
            new_items = new_clarifications[len(old_clarifications):]
            changes.append(("新增澄清", f"发布了 {len(new_items)} 条澄清"))
        
        old_qa = old_data.get("qa", [])
        new_qa = new_data.get("qa", [])
        if len(new_qa) > len(old_qa):
            new_items = new_qa[len(old_qa):]
            changes.append(("新增答疑", f"发布了 {len(new_items)} 条答疑"))
        
        old_attachments = old_data.get("attachments", [])
        new_attachments = new_data.get("attachments", [])
        if len(new_attachments) > len(old_attachments):
            new_items = new_attachments[len(old_attachments):]
            changes.append(("新增附件", f"添加了 {len(new_items)} 个附件"))
        
        # 检测时间变化
        if new_data.get("deadline") and new_data.get("deadline") != old_data.get("deadline"):
            changes.append(("截止时间变化", f"截止时间变为 {new_data.get('deadline')}"))
        
        return changes
    
    def _record_event(self, project_id: str, event_type: str, detail: str):
        """记录项目事件"""
        event = {
            "project_id": project_id,
            "project_title": self.tracked_projects.get(project_id, {}).get("title", ""),
            "event_type": event_type,
            "detail": detail,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.history.append(event)
        self._save_history()
    
    def get_recent_changes(self, hours: int = 24) -> List[Dict]:
        """
        获取最近 N 小时内的项目变化
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            最近的变化列表
        """
        now = datetime.now()
        recent = []
        
        for event in reversed(self.history):
            event_time = datetime.strptime(event["timestamp"], "%Y-%m-%d %H:%M:%S")
            if (now - event_time).total_seconds() < hours * 3600:
                recent.append(event)
            else:
                break
        
        return recent
    
    def get_project_timeline(self, project_id: str) -> List[Dict]:
        """获取项目的完整时间线"""
        return [h for h in self.history if h["project_id"] == project_id]
    
    def generate_tracking_report(self) -> str:
        """生成跟踪项目汇报"""
        if not self.tracked_projects:
            return "[汇报] 当前没有在跟踪的项目"
        
        report = f"\n{'='*70}\n"
        report += f"【项目跟踪汇报】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"{'='*70}\n\n"
        report += f"正在跟踪: {len(self.tracked_projects)} 个项目\n\n"
        
        for pid, proj in self.tracked_projects.items():
            report += f"【{pid}】{proj['title']}\n"
            report += f"  栏目: {proj['category']}\n"
            report += f"  状态: {proj['status']}\n"
            report += f"  发布: {proj['publish_time']}\n"
            report += f"  最后更新: {proj['last_update']}\n"
            
            # 显示该项目的最近变化
            timeline = self.get_project_timeline(pid)
            if timeline:
                recent = timeline[-3:]  # 最后3条事件
                report += f"  最近活动:\n"
                for event in recent:
                    report += f"    - {event['event_type']}: {event['detail']} ({event['timestamp']})\n"
            report += "\n"
        
        return report
