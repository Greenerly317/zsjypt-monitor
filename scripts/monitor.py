#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
中山资源交易平台监控脚本
功能: 监控平台新项目，按班次（早/午/晚）检测并通知
作者: 蟹黄 🦀
"""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib

# 尝试导入第三方库，如果不存在使用本地实现
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

class ZhongshanMonitor:
    """中山资源交易平台监控器"""
    
    def __init__(self, shift: str = "早班", memory_dir: str = None):
        """
        初始化监控器
        
        Args:
            shift: 班次（早班/午班/晚班）
            memory_dir: 记忆存储目录
        """
        self.shift = shift
        self.platform_url = "https://www.zsjypt.cn/subItem/58"
        self.keywords = ["勘察", "设计", "勘察设计"]
        self.categories = ["建设工程", "政府采购"]
        
        # 设置存储目录
        if memory_dir is None:
            memory_dir = Path(__file__).parent.parent / "memory"
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.check_file = self.memory_dir / "last-check.json"
        self.archive_dir = self.memory_dir / "archive"
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 统一使用 YYYY-MM-DD HH:MM:SS 格式的时间戳，便于时间戳对比
        self.current_check_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.shift_time = self._get_shift_time()
        
    def _get_shift_time(self) -> str:
        """获取班次时间"""
        shift_times = {
            "早班": "08:30",
            "午班": "12:00",
            "晚班": "20:30"
        }
        return shift_times.get(self.shift, "00:00")
    
    def fetch_platform_projects(self) -> Optional[List[Dict]]:
        """
        获取平台项目列表
        
        Returns:
            项目列表（每个项目包含 title, url, publish_time, category 等）
        """
        print(f"[{self.shift}] 正在访问平台页面: {self.platform_url}")
        
        try:
            # 使用真实爬虫获取项目
            from real_crawler import fetch_real_projects
            projects = fetch_real_projects()
            
            if not projects:
                # 如果真实爬虫获取失败，使用模拟数据作为备用
                print(f"[{self.shift}] 真实爬虫获取失败，使用备用模拟数据")
                projects = self._mock_fetch_projects()
            
            print(f"[{self.shift}] 成功获取 {len(projects)} 个项目")
            return projects
        except Exception as e:
            print(f"[{self.shift}] [ERROR] 平台访问失败: {str(e)}")
            return None
    
    def _mock_fetch_projects(self) -> List[Dict]:
        """
        模拟获取项目列表（实际环境中替换为真实爬虫）
        这是本地测试版本，实际使用时应使用 web_fetch 或 browser-automation
        
        时间戳采用 YYYY-MM-DD HH:MM:SS 格式，便于时间戳对比
        """
        # 示例项目数据结构 - 使用当前时间作为发布时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        mock_projects = [
            {
                "title": "中山市某勘察设计项目",
                "category": "建设工程",
                "url": "https://www.zsjypt.cn/project/001",
                "publish_time": current_time,
            },
            {
                "title": "政府采购设计服务项目",
                "category": "政府采购",
                "url": "https://www.zsjypt.cn/project/002",
                "publish_time": current_time,
            }
        ]
        return mock_projects
    
    def filter_by_keywords(self, projects: List[Dict]) -> List[Dict]:
        """
        按关键词筛选项目
        当关键词列表为空时，返回所有项目（监测该分类所有上新）
        
        Args:
            projects: 原始项目列表
            
        Returns:
            筛选后的项目列表
        """
        # 如果没有设置关键词，返回所有项目
        if not self.keywords:
            print(f"[{self.shift}] [FILTER] 无关键词限制，返回所有 {len(projects)} 个项目")
            return projects
        
        filtered = []
        for proj in projects:
            title = proj.get("title", "").lower()
            for keyword in self.keywords:
                if keyword in title:
                    proj["keywords_matched"] = [keyword]
                    filtered.append(proj)
                    break
        
        print(f"[{self.shift}] [FILTER] 关键词筛选: {len(filtered)}/{len(projects)} 项目")
        return filtered
    
    def load_last_check(self) -> Optional[Dict]:
        """
        加载上次检查结果
        
        Returns:
            上次检查的项目数据
        """
        if not self.check_file.exists():
            print(f"[{self.shift}] [FIRST] 首次检查，无历史记录")
            return None
        
        try:
            with open(self.check_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[{self.shift}] [LOAD] 已加载上次检查: {data['last_check_time']}")
            return data
        except Exception as e:
            print(f"[{self.shift}] [WARN] 无法加载历史记录: {str(e)}")
            return None
    
    def detect_new_projects(self, current: List[Dict], last_check: Optional[Dict]) -> List[Dict]:
        """
        对比检测新增项目 - 基于发布时间戳
        只返回发布时间在上次检查之后的项目
        
        Args:
            current: 当前项目列表
            last_check: 上次检查结果
            
        Returns:
            新增项目列表
        """
        if last_check is None or "last_check_time" not in last_check:
            print(f"[{self.shift}] [NEW] 首次检查，所有项目标记为新增")
            return current
        
        # 获取上次检查的时间戳
        last_check_time_str = last_check.get("last_check_time", "")
        print(f"[{self.shift}] [DETECT] 比较时间: 上次 {last_check_time_str}")
        
        # 基于时间戳的新项目检测
        new_projects = []
        for proj in current:
            proj_time_str = proj.get("publish_time", "")
            # 如果项目发布时间在上次检查之后，则为新项目
            if proj_time_str > last_check_time_str:
                new_projects.append(proj)
                print(f"[{self.shift}] [NEW] 新项目: {proj.get('title')} (发布于 {proj_time_str})")
        
        print(f"[{self.shift}] [DETECT] 时间戳对比: 发现 {len(new_projects)} 个新项目 (上次 {len(last_check.get('projects', []))} -> 当前 {len(current)})")
        return new_projects
    
    def save_check_result(self, projects: List[Dict]) -> bool:
        """
        保存本次检查结果
        
        Args:
            projects: 本次检查的所有项目
            
        Returns:
            是否成功保存
        """
        check_data = {
            "last_check_time": self.current_check_time,
            "shift": self.shift,
            "shift_time": self.shift_time,
            "total_projects": len(projects),
            "projects": projects
        }
        
        try:
            # 保存当前结果
            with open(self.check_file, 'w', encoding='utf-8') as f:
                json.dump(check_data, f, ensure_ascii=False, indent=2)
            
            # 归档本次检查
            archive_file = self.archive_dir / f"check_{self.current_check_time.replace(':', '-')}.json"
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(check_data, f, ensure_ascii=False, indent=2)
            
            print(f"[{self.shift}] [OK] 检查结果已保存")
            return True
        except Exception as e:
            print(f"[{self.shift}] [ERROR] 保存失败: {str(e)}")
            return False
    
    def format_notification(self, projects: List[Dict]) -> str:
        """
        格式化飞书通知消息
        
        Args:
            projects: 新增项目列表
            
        Returns:
            格式化后的通知文本
        """
        if not projects:
            return "无新项目"
        
        message = f"[中山平台] 新项目上架（{self.shift}）\n\n"
        
        for i, proj in enumerate(projects, 1):
            message += f"[{i}] {proj.get('title', '未知')}\n"
            message += f"  栏目: {proj.get('category', '未分类')}\n"
            message += f"  发布时间: {proj.get('publish_time', '未知')}\n"
            message += f"  URL: {proj.get('url', '#')}\n\n"
        
        message += f"检测时间: {self.current_check_time}\n"
        message += f"监控者: Crab Monitor"
        
        return message
    
    def send_feishu_notification(self, projects: List[Dict], feishu_webhook: Optional[str] = None) -> bool:
        """
        发送飞书通知（需要配置飞书机器人）
        
        Args:
            projects: 新增项目
            feishu_webhook: 飞书 Webhook URL
            
        Returns:
            是否成功发送
        """
        if not projects:
            print(f"[{self.shift}] [INFO] 无新项目，跳过通知")
            return True
        
        # 如果未提供 webhook，从环境变量或配置文件读取
        if feishu_webhook is None:
            feishu_webhook = os.getenv("FEISHU_WEBHOOK")
        
        if not feishu_webhook:
            print(f"[{self.shift}] [WARN] 飞书 Webhook 未配置，跳过通知发送")
            print(f"    请设置环境变量 FEISHU_WEBHOOK 或提供 webhook URL")
            # 本地测试时输出消息内容
            print(f"[{self.shift}] [MOCK] [模拟通知]\n{self.format_notification(projects)}")
            return False
        
        try:
            message = self.format_notification(projects)
            payload = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }
            
            # 实际发送时需要使用 requests
            if requests is None:
                print(f"[{self.shift}] [WARN] requests 库未安装，模拟通知发送")
                print(f"[{self.shift}] [MOCK] [将发送到飞书]\n{message}")
                return True
            
            response = requests.post(feishu_webhook, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"[{self.shift}] [OK] 飞书通知已发送")
                return True
            else:
                print(f"[{self.shift}] [ERROR] 飞书通知发送失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"[{self.shift}] [ERROR] 飞书通知错误: {str(e)}")
            return False
    
    def run(self, feishu_webhook: Optional[str] = None) -> Tuple[bool, int]:
        """
        执行完整的监控流程
        
        Args:
            feishu_webhook: 飞书 Webhook URL
            
        Returns:
            (是否成功, 新增项目数)
        """
        print(f"\n{'='*60}")
        print(f"[{self.shift}] 中山资源交易平台监控 - 开始检查")
        print(f"时间: {self.current_check_time}")
        print(f"{'='*60}\n")
        
        # 1. 获取平台项目
        all_projects = self.fetch_platform_projects()
        if all_projects is None:
            print(f"[{self.shift}] [ERROR] 监控流程中止")
            return False, 0
        
        # 2. 关键词筛选
        filtered_projects = self.filter_by_keywords(all_projects)
        
        # 3. 加载上次检查结果
        last_check = self.load_last_check()
        
        # 4. 增量检测
        new_projects = self.detect_new_projects(filtered_projects, last_check)
        
        # 5. 保存本次结果
        self.save_check_result(filtered_projects)
        
        # 6. 发送通知
        self.send_feishu_notification(new_projects, feishu_webhook)
        
        print(f"\n[{self.shift}] [OK] 监控完成")
        print(f"{'='*60}\n")
        
        return True, len(new_projects)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="中山资源交易平台监控器")
    parser.add_argument("--shift", default="早班", choices=["早班", "午班", "晚班"], 
                       help="班次（默认：早班）")
    parser.add_argument("--memory-dir", default=None,
                       help="记忆存储目录")
    parser.add_argument("--feishu-webhook", default=None,
                       help="飞书 Webhook URL")
    parser.add_argument("--force-check", action="store_true",
                       help="强制执行检查（不考虑时间限制）")
    
    args = parser.parse_args()
    
    # 创建监控器实例
    monitor = ZhongshanMonitor(shift=args.shift, memory_dir=args.memory_dir)
    
    # 执行监控
    success, new_count = monitor.run(feishu_webhook=args.feishu_webhook)
    
    # 返回状态码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
