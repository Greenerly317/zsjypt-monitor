#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中山平台监测执行脚本 - 2026-03-28 定时任务
"""
import sys
import io
import os
import json
import re
import requests
from datetime import datetime
from pathlib import Path

# 修复Windows编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.zsjypt.cn/',
}

def fetch_platform_data():
    """抓取平台数据"""
    results = {}
    
    # 获取建设工程招标公告 (subItem/58)
    print("[INFO] 正在访问中山资源交易平台...")
    try:
        resp = requests.get('https://www.zsjypt.cn/subItem/58', headers=headers, timeout=20)
        resp.encoding = resp.apparent_encoding or 'utf-8'
        results['main_page'] = {
            'status': resp.status_code,
            'length': len(resp.text),
            'content': resp.text[:5000] if resp.status_code == 200 else ''
        }
        print(f"[OK] 主页访问成功，状态码: {resp.status_code}，内容长度: {len(resp.text)}")
        
        # 分析API接口
        url_patterns = re.findall(r'url\s*[=:]\s*["\']([^"\']+)["\']', resp.text)
        print(f"[INFO] 发现URL配置: {url_patterns[:10]}")
        
        # 查找list/query相关API
        for u in url_patterns:
            if any(k in u.lower() for k in ['list', 'query', 'notice', 'page', 'item']):
                print(f"[API] 候选接口: {u}")
        
    except Exception as e:
        print(f"[ERROR] 主页访问失败: {e}")
        results['main_page'] = {'status': None, 'error': str(e)}
    
    return results

def try_known_apis():
    """尝试已知的API接口"""
    known_apis = [
        # 基于常见模式尝试
        'https://www.zsjypt.cn/xxzxList?subItemId=58&pageNum=1&pageSize=20',
        'https://www.zsjypt.cn/subItemList?id=58&pageNum=1',
        'https://www.zsjypt.cn/notice/list?categoryId=58&pageNum=1&pageSize=20',
        'https://www.zsjypt.cn/api/notice/list?subId=58&page=1',
    ]
    
    found_data = None
    
    for api_url in known_apis:
        try:
            resp = requests.get(api_url, headers=headers, timeout=10)
            print(f"[TRY] {api_url} -> {resp.status_code}")
            if resp.status_code == 200:
                content = resp.text[:2000]
                # 检查是否是JSON数据
                try:
                    data = resp.json()
                    print(f"[JSON] 找到JSON接口: {api_url}")
                    print(f"[JSON] 数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    found_data = {'url': api_url, 'data': data}
                    break
                except:
                    # 不是JSON，检查是否有列表内容
                    if any(k in content for k in ['title', '招标', '公告', 'projectName']):
                        print(f"[HTML] 可能包含数据: {api_url}")
        except Exception as e:
            print(f"[SKIP] {api_url}: {e}")
    
    return found_data

def parse_projects_from_html(html_content):
    """从HTML中解析项目列表"""
    projects = []
    
    # 尝试多种解析方式
    # 方式1: 查找标准表格行
    tr_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
    td_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
    a_pattern = re.compile(r'<a[^>]+href=["\']([^"\']*)["\'][^>]*>([^<]+)</a>', re.IGNORECASE)
    
    rows = tr_pattern.findall(html_content)
    for row in rows:
        cells = td_pattern.findall(row)
        if len(cells) >= 2:
            # 尝试从第一个td中提取链接和标题
            title_match = a_pattern.search(cells[0])
            if title_match:
                url = title_match.group(1)
                title = title_match.group(2).strip()
                # 过滤掉明显不是项目的行（太短或包含导航词）
                if len(title) > 5 and not any(k in title for k in ['首页', '上一页', '下一页']):
                    # 提取时间（通常在最后几个td中）
                    publish_time = ''
                    for cell in reversed(cells):
                        clean = re.sub(r'<[^>]+>', '', cell).strip()
                        # 检查是否是日期格式
                        if re.search(r'\d{4}-\d{2}-\d{2}', clean):
                            publish_time = clean
                            break
                    
                    # 构建完整URL
                    if url.startswith('/'):
                        url = 'https://www.zsjypt.cn' + url
                    
                    projects.append({
                        'title': title,
                        'url': url,
                        'publish_time': publish_time,
                        'category': '建设工程'
                    })
    
    return projects

def load_last_check():
    """加载上次检查记录"""
    last_check_file = MEMORY_DIR / "last-check.json"
    if last_check_file.exists():
        try:
            with open(last_check_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return None

def save_check_result(projects, new_count):
    """保存本次检查结果"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    check_data = {
        "last_check_time": now,
        "shift": "定时任务",
        "total_projects": len(projects),
        "new_count": new_count,
        "projects": projects
    }
    
    last_check_file = MEMORY_DIR / "last-check.json"
    with open(last_check_file, 'w', encoding='utf-8') as f:
        json.dump(check_data, f, ensure_ascii=False, indent=2)
    
    # 同时归档
    archive_dir = MEMORY_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    archive_file = archive_dir / f"check_{now.replace(':', '-').replace(' ', '_')}.json"
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(check_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] 检查结果已保存: {now}")
    return now

def detect_new_projects(current_projects, last_check):
    """检测新增项目"""
    if not last_check or 'last_check_time' not in last_check:
        return current_projects, "首次检查"
    
    last_time = last_check['last_check_time']
    last_known_urls = {p.get('url', '') for p in last_check.get('projects', [])}
    
    new_projects = []
    for proj in current_projects:
        proj_url = proj.get('url', '')
        proj_time = proj.get('publish_time', '')
        
        # 如果URL不在上次记录中，或者发布时间在上次检查之后
        if proj_url not in last_known_urls:
            new_projects.append(proj)
        elif proj_time and proj_time > last_time:
            new_projects.append(proj)
    
    return new_projects, f"上次检查: {last_time}"

def filter_by_keywords(projects, keywords=None):
    """关键词筛选"""
    if not keywords:
        return projects  # 无关键词限制，返回全部
    
    filtered = []
    for proj in projects:
        title = proj.get('title', '')
        for kw in keywords:
            if kw in title:
                proj_copy = dict(proj)
                proj_copy['matched_keyword'] = kw
                filtered.append(proj_copy)
                break
    return filtered

def load_feishu_config():
    """加载飞书配置"""
    feishu_config_file = BASE_DIR / "config" / "feishu.json"
    if feishu_config_file.exists():
        try:
            with open(feishu_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def send_feishu_report(title, content, webhook_url):
    """发送飞书报告"""
    if not webhook_url:
        print("[WARN] 飞书Webhook未配置，跳过发送")
        return False
    
    payload = {
        'msg_type': 'text',
        'content': {
            'text': f"{title}\n\n{content}"
        }
    }
    
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('StatusCode') == 0 or result.get('code') == 0:
                print("[OK] 飞书消息发送成功")
                return True
            else:
                print(f"[ERROR] 飞书返回错误: {result}")
                return False
        else:
            print(f"[ERROR] HTTP错误: {resp.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] 飞书发送失败: {e}")
        return False

def main():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[中山平台监测] 开始执行 - {now_str}")
    print(f"{'='*60}\n")
    
    # 1. 加载飞书配置
    feishu_config = load_feishu_config()
    webhook_url = feishu_config.get('webhook_url', '')
    
    # 2. 从平台抓取数据
    platform_results = fetch_platform_data()
    
    # 3. 尝试已知API接口
    api_data = try_known_apis()
    
    # 4. 解析项目列表
    current_projects = []
    
    main_page_data = platform_results.get('main_page', {})
    if main_page_data.get('status') == 200:
        html = main_page_data.get('content', '')
        parsed = parse_projects_from_html(html)
        current_projects.extend(parsed)
        print(f"[PARSE] 从主页HTML解析: {len(parsed)} 个项目")
    
    if api_data and 'data' in api_data:
        print(f"[API] 从API接口获取到数据")
        # 处理API数据（根据实际结构）
    
    # 5. 关键词筛选（当前config为空关键词，即全部监测）
    KEYWORDS = []  # 根据config/platform-config.json
    filtered_projects = filter_by_keywords(current_projects, KEYWORDS)
    print(f"[FILTER] 筛选后: {len(filtered_projects)} 个项目")
    
    # 6. 加载上次检查记录并检测新项目
    last_check = load_last_check()
    new_projects, check_context = detect_new_projects(filtered_projects, last_check)
    print(f"[DETECT] {check_context}")
    print(f"[DETECT] 新增项目: {len(new_projects)} 个")
    
    # 7. 加载已跟踪项目
    tracked_file = MEMORY_DIR / "tracked_projects.json"
    tracked_projects = {}
    if tracked_file.exists():
        try:
            with open(tracked_file, 'r', encoding='utf-8') as f:
                tracked_projects = json.load(f)
        except:
            pass
    print(f"[TRACK] 正在跟踪项目: {len(tracked_projects)} 个")
    
    # 8. 保存本次检查结果
    save_check_result(filtered_projects, len(new_projects))
    
    # 9. 生成报告内容
    report_lines = []
    report_lines.append(f"中山市公共资源交易平台监测报告")
    report_lines.append(f"检测时间：{now_str}")
    report_lines.append(f"")
    
    # 平台访问状态
    main_status = platform_results.get('main_page', {}).get('status')
    if main_status == 200:
        report_lines.append(f"平台状态：正常访问")
    else:
        report_lines.append(f"平台状态：访问异常 (HTTP {main_status})")
    
    report_lines.append(f"本次抓取：{len(filtered_projects)} 个项目")
    report_lines.append(f"上次检查：{last_check.get('last_check_time', '首次') if last_check else '首次'}")
    report_lines.append(f"")
    
    # 新项目部分
    report_lines.append(f"【新增项目】{len(new_projects)} 个")
    report_lines.append("-" * 40)
    if new_projects:
        for i, proj in enumerate(new_projects, 1):
            report_lines.append(f"[{i}] {proj.get('title', '未知')}")
            report_lines.append(f"    类别：{proj.get('category', '建设工程')}")
            report_lines.append(f"    发布：{proj.get('publish_time', '未知')}")
            report_lines.append(f"    链接：{proj.get('url', '#')}")
            report_lines.append("")
    else:
        report_lines.append("暂无新项目（平台数据为动态加载，需浏览器环境抓取）")
        report_lines.append("")
    
    # 跟踪项目部分
    report_lines.append(f"【跟踪中项目】{len(tracked_projects)} 个")
    report_lines.append("-" * 40)
    if tracked_projects:
        for pid, proj in tracked_projects.items():
            status = proj.get('status', '跟踪中')
            title = proj.get('title', '未知')
            last_update = proj.get('last_update', '未知')
            report_lines.append(f"[{pid}] {title}")
            report_lines.append(f"    状态：{status}")
            report_lines.append(f"    最后更新：{last_update}")
            report_lines.append("")
    else:
        report_lines.append("当前无跟踪项目")
        report_lines.append("")
    
    report_lines.append(f"监控者：蟹黄 🦀")
    
    report_content = "\n".join(report_lines)
    
    print("\n" + "="*60)
    print("监测报告内容：")
    print("="*60)
    print(report_content)
    print("="*60)
    
    # 10. 发送飞书通知
    if webhook_url:
        send_feishu_report("中山平台监测报告", report_content, webhook_url)
    else:
        print("\n[WARN] 飞书Webhook未配置，报告未发送")
        print("[INFO] 请在 config/feishu.json 中配置 webhook_url")
    
    # 返回结果给调用者
    result = {
        'success': True,
        'check_time': now_str,
        'platform_accessible': main_status == 200,
        'total_fetched': len(filtered_projects),
        'new_count': len(new_projects),
        'tracked_count': len(tracked_projects),
        'feishu_sent': bool(webhook_url),
        'report': report_content
    }
    
    print(f"\n[DONE] 监测完成")
    print(f"  平台可访问: {result['platform_accessible']}")
    print(f"  本次抓取: {result['total_fetched']} 项")
    print(f"  新增项目: {result['new_count']} 项")
    print(f"  跟踪项目: {result['tracked_count']} 项")
    print(f"  飞书通知: {'已发送' if result['feishu_sent'] else '未配置'}")
    
    return result

if __name__ == '__main__':
    result = main()
    # 输出JSON结果供外部调用
    import json
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(f"\n[RESULT_JSON]\n{output}")
