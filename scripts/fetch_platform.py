#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取中山资源交易平台项目数据"""

import requests
import json
import re
import sys
from datetime import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.zsjypt.cn/',
}

def fetch_page(url, params=None):
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.status_code, resp.text
    except Exception as e:
        return None, str(e)

# 主监控URL
urls_to_try = [
    'https://www.zsjypt.cn/subItem/58',  # 建设工程招标公告
    'https://www.zsjypt.cn/xxzxList/58', # 可能的列表API
    'https://www.zsjypt.cn/api/notices',
]

# 先试主页
status, content = fetch_page('https://www.zsjypt.cn/subItem/58')
print(f"主页 Status: {status}")
print(f"Content length: {len(content) if content else 0}")
if content:
    print("=== 内容预览 (前3000字) ===")
    print(content[:3000])
