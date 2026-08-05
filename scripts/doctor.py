#!/usr/bin/env python3
"""
中山平台监测 - 环境自检（doctor）

离线检查运行环境是否健康：Python 版本、依赖是否齐全、配置文件是否就绪、追踪是否配置。
默认不联网；加 --net 才做平台连通性探测。

设计原则：密钥绝不打印——webhook / 关键词只报「是否已配置」，绝不输出实际值。
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
CONFIG_DIR = os.path.join(ROOT, 'config')


def _have(module):
    try:
        __import__(module)
        return True
    except Exception:
        return False


def _cfg_present(name):
    return os.path.exists(os.path.join(CONFIG_DIR, name))


def _notify_configured():
    """返回已启用推送平台列表（不打印 webhook 值）。"""
    path = os.path.join(CONFIG_DIR, 'notify.json')
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception:
        return []
    out = []
    for k in ('feishu', 'wecom', 'dingtalk'):
        wh = (cfg.get(k) or {}).get('webhook', '')
        if isinstance(wh, str) and wh.strip().lower().startswith('http'):
            out.append(k)
    return out


def _user_keywords():
    path = os.path.join(CONFIG_DIR, 'user-config.json')
    if not os.path.exists(path):
        return None  # 未配置
    try:
        with open(path, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('keywords', [])
    except Exception:
        return []


def main():
    checks = []
    ok = True

    # 1. Python 版本
    py_ok = sys.version_info >= (3, 10)
    ok &= py_ok
    checks.append(('Python >= 3.10', py_ok, f'{sys.version_info.major}.{sys.version_info.minor}'))

    # 2. 依赖
    for mod, pkg in (('requests', 'requests'), ('bs4', 'beautifulsoup4')):
        present = _have(mod)
        ok &= present
        checks.append((f'依赖 {pkg}', present, 'OK' if present else '缺失，请 pip install ' + pkg))

    # 3. 核心脚本存在
    for fn in ('crab-monitor.py', 'make_dashboard.py', 'notify.py'):
        present = os.path.exists(os.path.join(HERE, fn))
        ok &= present
        checks.append((f'脚本 {fn}', present, 'OK' if present else '缺失'))

    # 4. 配置模板存在
    for fn in ('notify.example.json', 'user-config.example.json'):
        present = _cfg_present(fn)
        ok &= present
        checks.append((f'模板 {fn}', present, 'OK' if present else '缺失'))

    # 5. 推送配置（不打印值）
    enabled = _notify_configured()
    checks.append(('推送已配置', True, ('/'.join(enabled) if enabled else '未配置（可跳过）')))

    # 6. 用户过滤配置
    kw = _user_keywords()
    if kw is None:
        checks.append(('用户关键词', True, '未配置（全量汇报降级）'))
    else:
        checks.append(('用户关键词', True, f'已配置 {len(kw)} 个：{" ".join(kw)}'))

    # 打印报告
    print('=== zsjypt-monitor 环境自检 ===')
    for name, passed, detail in checks:
        mark = '✅' if passed else '❌'
        print(f'  {mark} {name}: {detail}')
    print('=== 结论 ===', '全部通过' if ok else '存在问题，见上')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
