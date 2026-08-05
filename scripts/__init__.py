# -*- coding: utf-8 -*-
"""
中山资源交易平台监控 Skill 包初始化
"""

__version__ = "1.0.0"
__author__ = "蟹黄 🦀"
__description__ = "中山市公共资源交易平台项目监控"

# 导出主要类
try:
    from .monitor import ZhongshanMonitor
    from .feishu_notifier import FeishuNotifier, FeishuConfig
except ImportError:
    pass

__all__ = [
    "ZhongshanMonitor",
    "FeishuNotifier",
    "FeishuConfig",
]
