#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中山平台监测 - 完整执行脚本（已验证API接口）
API: POST https://www.zsjypt.cn/pageList
参数: page=1, limit=20, nodeId=58 (form格式)
字段: arab01=ID, arab04=标题, arab32=发布时间
"""
import sys, io, requests, re, json
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent.parent
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

BASE_URL = "https://www.zsjypt.cn"
NODE_ID = 58  # 建设工程招标公告

FORM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://www.zsjypt.cn/subItem/58',
    'X-Requested-With': 'XMLHttpRequest',
}

def fetch_all_projects(max_pages=3):
    """获取所有项目（最多前N页）"""
    all_projects = []
    total = None
    
    for page in range(1, max_pages + 1):
        params = {
            'page': page,
            'limit': 50,
            'nodeId': NODE_ID
        }
        
        try:
            resp = requests.post(
                f'{BASE_URL}/pageList',
                data=params,
                headers=FORM_HEADERS,
                timeout=15
            )
            
            if resp.status_code != 200:
                print(f'[ERROR] 第{page}页请求失败: {resp.status_code}')
                break
            
            data = resp.json()
            if data.get('code') != 0:
                print(f'[ERROR] API返回错误: {data.get("msg")}')
                break
            
            result = data.get('data', {})
            page_data = result.get('list', result.get('records', result.get('rows', [])))
            
            if total is None:
                total = result.get('total', 0)
                print(f'[INFO] 平台总项目数: {total}')
            
            if not page_data:
                break
            
            # 转换数据格式
            for item in page_data:
                project = {
                    'id': str(item.get('arab01', '')),
                    'title': item.get('arab04', ''),
                    'category': '建设工程',
                    'publish_time': item.get('arab32', '').replace('.0', '') if item.get('arab32') else '',
                    'deadline': item.get('arab25', '').replace('.0', '') if item.get('arab25') else '',
                    'open_bid_time': item.get('arab26', '').replace('.0', '') if item.get('arab26') else '',
                    'url': f"{BASE_URL}/detail/{item.get('arab01', '')}",
                    'raw': item
                }
                # 清理时间格式
                for tfield in ['publish_time', 'deadline', 'open_bid_time']:
                    if project[tfield]:
                        project[tfield] = project[tfield].strip()[:19]  # 只保留到秒
                
                all_projects.append(project)
            
            print(f'[INFO] 第{page}页: 获取 {len(page_data)} 条，累计 {len(all_projects)} 条')
            
            # 如果已经拿够了足够多的数据就停止
            if len(all_projects) >= 100:
                break
                
        except Exception as e:
            print(f'[ERROR] 第{page}页请求异常: {e}')
            break
    
    return all_projects, total

def filter_by_keywords(projects, keywords=None):
    """关键词筛选"""
    if not keywords:
        return projects
    
    filtered = []
    for proj in projects:
        title = proj.get('title', '')
        for kw in keywords:
            if kw in title:
                proj = dict(proj)
                proj['matched_keyword'] = kw
                filtered.append(proj)
                break
    return filtered

def load_last_check():
    """加载上次检查记录"""
    f = MEMORY_DIR / "last-check.json"
    if f.exists():
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                return json.load(fp)
        except:
            pass
    return None

def save_check_result(projects, new_count, total_platform):
    """保存本次检查结果"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    check_data = {
        "last_check_time": now,
        "shift": "定时任务",
        "total_platform": total_platform,
        "total_fetched": len(projects),
        "new_count": new_count,
        "projects": [
            {"id": p["id"], "title": p["title"], "url": p["url"], "publish_time": p["publish_time"]}
            for p in projects
        ]
    }
    
    f = MEMORY_DIR / "last-check.json"
    with open(f, 'w', encoding='utf-8') as fp:
        json.dump(check_data, fp, ensure_ascii=False, indent=2)
    
    # 归档
    archive_dir = MEMORY_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    af = archive_dir / f"check_{now.replace(':', '-').replace(' ', '_')}.json"
    with open(af, 'w', encoding='utf-8') as fp:
        json.dump(check_data, fp, ensure_ascii=False, indent=2)
    
    print(f'[OK] 检查结果已保存: {now}')
    return now

def detect_new_projects(current, last_check):
    """检测新项目"""
    if not last_check:
        print('[INFO] 首次检查，所有项目均视为新增')
        return current, '首次检查'
    
    last_time = last_check.get('last_check_time', '')
    last_ids = {p.get('id', '') for p in last_check.get('projects', [])}
    
    new_projects = []
    for proj in current:
        pid = proj.get('id', '')
        pub_time = proj.get('publish_time', '')
        
        # 判断：ID不在上次记录中，且发布时间在上次检查之后
        if pid not in last_ids and pub_time > last_time[:10]:  # 比较日期部分
            new_projects.append(proj)
    
    return new_projects, f'上次检查: {last_time}'

def load_feishu_config():
    """加载飞书配置"""
    f = BASE_DIR / "config" / "feishu.json"
    if f.exists():
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                return json.load(fp)
        except:
            pass
    return {}

def send_feishu(title, content, webhook_url):
    """发送飞书消息"""
    if not webhook_url:
        return False
    
    payload = {
        'msg_type': 'text',
        'content': {'text': f'{title}\n\n{content}'}
    }
    
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('StatusCode') == 0 or result.get('code') == 0:
                print('[OK] 飞书消息发送成功')
                return True
            else:
                print(f'[ERROR] 飞书返回: {result}')
                return False
        else:
            print(f'[ERROR] 飞书HTTP: {resp.status_code}')
            return False
    except Exception as e:
        print(f'[ERROR] 飞书发送失败: {e}')
        return False

def main():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f'\n{"="*60}')
    print(f'[中山平台监测] 开始执行 - {now_str}')
    print(f'{"="*60}\n')
    
    # 加载飞书配置
    feishu_cfg = load_feishu_config()
    webhook_url = feishu_cfg.get('webhook_url', '')
    
    # 抓取平台数据
    print('[STEP 1] 抓取平台数据...')
    current_projects, total_count = fetch_all_projects(max_pages=3)
    print(f'[INFO] 共获取 {len(current_projects)} 个项目（平台总计 {total_count} 个）')
    
    # 关键词筛选（当前无限制，全部返回）
    KEYWORDS = []  # 可配置: ['勘察', '设计', '勘察设计']
    filtered = filter_by_keywords(current_projects, KEYWORDS)
    print(f'[INFO] 关键词筛选后: {len(filtered)} 个项目')
    
    # 加载上次检查
    print('\n[STEP 2] 对比历史数据...')
    last_check = load_last_check()
    new_projects, check_ctx = detect_new_projects(filtered, last_check)
    print(f'[INFO] {check_ctx}')
    print(f'[INFO] 发现新项目: {len(new_projects)} 个')
    
    # 加载跟踪项目
    tracked_data = {}
    tf = MEMORY_DIR / "tracked_projects.json"
    if tf.exists():
        try:
            with open(tf, 'r', encoding='utf-8') as fp:
                tracked_data = json.load(fp)
        except:
            pass
    print(f'[INFO] 正在跟踪项目: {len(tracked_data)} 个')
    
    # 保存本次检查结果
    save_check_result(filtered, len(new_projects), total_count)
    
    # 生成报告
    print('\n[STEP 3] 生成监测报告...')
    lines = []
    lines.append(f'中山市公共资源交易平台 · 监测报告')
    lines.append(f'{"="*50}')
    lines.append(f'检测时间：{now_str}')
    lines.append(f'平台总项目：{total_count} 个')
    lines.append(f'本次抓取：{len(filtered)} 个（前3页）')
    lines.append(f'上次检查：{last_check.get("last_check_time", "首次") if last_check else "首次"}')
    lines.append(f'')
    
    # 新项目
    lines.append(f'【新增项目】共 {len(new_projects)} 个')
    lines.append(f'{"-"*40}')
    if new_projects:
        for i, p in enumerate(new_projects[:10], 1):
            lines.append(f'[{i}] {p["title"]}')
            lines.append(f'    发布时间：{p["publish_time"]}')
            lines.append(f'    链接：{p["url"]}')
            lines.append(f'')
        if len(new_projects) > 10:
            lines.append(f'  ... 还有 {len(new_projects)-10} 个新项目未显示')
    else:
        lines.append(f'今日无新项目（相比上次检查 {check_ctx}）')
    lines.append(f'')
    
    # 最近项目（最新5条）
    lines.append(f'【最新项目（Top 5）】')
    lines.append(f'{"-"*40}')
    for i, p in enumerate(filtered[:5], 1):
        lines.append(f'[{i}] {p["title"]}')
        lines.append(f'    发布：{p["publish_time"]}')
        lines.append(f'')
    
    # 跟踪项目
    lines.append(f'【跟踪中项目】共 {len(tracked_data)} 个')
    lines.append(f'{"-"*40}')
    if tracked_data:
        for pid, proj in tracked_data.items():
            lines.append(f'  [{pid}] {proj.get("title", "未知")}')
            lines.append(f'      状态：{proj.get("status", "跟踪中")}')
            lines.append(f'      最后更新：{proj.get("last_update", "未知")}')
    else:
        lines.append(f'  当前无跟踪项目')
    lines.append(f'')
    lines.append(f'监控者：蟹黄 🦀 | 数据来源：中山市公共资源交易平台')
    
    report_content = '\n'.join(lines)
    
    print('\n' + '='*60)
    print('完整报告：')
    print('='*60)
    print(report_content)
    print('='*60)
    
    # 发送飞书
    print('\n[STEP 4] 发送飞书通知...')
    if webhook_url:
        feishu_ok = send_feishu('🔔 中山平台监测报告', report_content, webhook_url)
    else:
        print('[WARN] 飞书Webhook未配置，跳过发送')
        feishu_ok = False
    
    # 汇总结果
    result = {
        'success': True,
        'check_time': now_str,
        'total_platform': total_count,
        'total_fetched': len(filtered),
        'new_count': len(new_projects),
        'tracked_count': len(tracked_data),
        'feishu_sent': feishu_ok,
        'new_projects': [{'title': p['title'], 'publish_time': p['publish_time']} for p in new_projects[:10]],
        'latest_5': [{'title': p['title'], 'publish_time': p['publish_time']} for p in filtered[:5]],
        'report': report_content
    }
    
    print(f'\n[DONE] 监测完成！')
    print(f'  平台总项目: {result["total_platform"]}')
    print(f'  本次抓取: {result["total_fetched"]} 项')
    print(f'  新增项目: {result["new_count"]} 项')
    print(f'  跟踪项目: {result["tracked_count"]} 项')
    print(f'  飞书通知: {"已发送" if result["feishu_sent"] else "未配置"}')
    
    return result

if __name__ == '__main__':
    result = main()
