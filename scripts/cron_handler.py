#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenClaw 定时任务集成脚本
用于每日三班制自动执行监控任务
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加脚本目录到 Python 路径
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from monitor import ZhongshanMonitor
from feishu_notifier import FeishuConfig, FeishuNotifier


class CronTaskRunner:
    """定时任务运行器"""
    
    SHIFTS = {
        "早班": {"time": "08:30", "description": "上班前检查"},
        "午班": {"time": "12:00", "description": "中午检查"},
        "晚班": {"time": "20:30", "description": "下班后检查"}
    }
    
    def __init__(self):
        self.memory_dir = SKILL_DIR / "memory"
        self.log_dir = SKILL_DIR / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def get_current_shift(self) -> str:
        """获取当前班次"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 根据当前时间判断班次
        if "08:" in current_time or (current_time.startswith("08") and int(current_time[3:]) >= 30):
            return "早班"
        elif "12:" in current_time or (current_time.startswith("12") and int(current_time[3:]) < 30):
            return "午班"
        elif "20:" in current_time or (current_time.startswith("20") and int(current_time[3:]) >= 30):
            return "晚班"
        else:
            return "早班"  # 默认
    
    def run_check(self, shift: str = None, force_notify: bool = True) -> bool:
        """
        执行检查
        
        Args:
            shift: 班次（默认为当前班次）
            force_notify: 是否强制发送通知
            
        Returns:
            是否成功
        """
        if shift is None:
            shift = self.get_current_shift()
        
        print(f"\n[OpenClaw] 触发监控任务 - {shift}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        # 加载飞书配置
        feishu_config = FeishuConfig.load()
        feishu_webhook = feishu_config.get("webhook_url")
        
        # 创建监控器
        monitor = ZhongshanMonitor(shift=shift, memory_dir=str(self.memory_dir))
        
        # 执行监控
        success, new_count = monitor.run(feishu_webhook=feishu_webhook if force_notify else None)
        
        # 记录日志
        self.log_result(shift, success, new_count)
        
        return success
    
    def log_result(self, shift: str, success: bool, new_count: int):
        """
        记录执行结果
        
        Args:
            shift: 班次
            success: 是否成功
            new_count: 新增项目数
        """
        log_file = self.log_dir / f"monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "shift": shift,
            "success": success,
            "new_projects": new_count,
            "status": "成功" if success else "失败"
        }
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"⚠️  日志记录失败: {str(e)}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 定时任务执行器")
    parser.add_argument(
        "--shift",
        type=str,
        default=None,
        choices=["早班", "午班", "晚班"],
        help="班次（默认为当前班次）"
    )
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="禁用飞书通知"
    )
    
    args = parser.parse_args()
    
    runner = CronTaskRunner()
    success = runner.run_check(
        shift=args.shift,
        force_notify=not args.no_notify
    )
    
    return 0 if success else 1


# 如果由 OpenClaw 调用，需要这样的格式
def openclaw_handler(event, context):
    """OpenClaw 事件处理器"""
    try:
        # 从事件中提取班次信息
        shift = event.get("shift", None)
        
        runner = CronTaskRunner()
        success = runner.run_check(shift=shift)
        
        return {
            "statusCode": 200 if success else 500,
            "body": json.dumps({
                "message": "检查完成",
                "success": success
            })
        }
    except Exception as e:
        print(f"❌ OpenClaw 执行失败: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": f"执行错误: {str(e)}",
                "success": False
            })
        }


if __name__ == "__main__":
    sys.exit(main())
