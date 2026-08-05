#!/usr/bin/env python3
"""
中山公共资源交易平台监控脚本
用法：
  python crab-monitor.py              # 日常汇报
  python crab-monitor.py track 关键词   # 添加关注项目
  python crab-monitor.py untrack 关键词 # 移除关注
  python crab-monitor.py list          # 列出当前关注
"""

import os, requests, json, sys
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = 'https://www.zsjypt.cn'
PAGE_LIST_URL = f'{BASE_URL}/pageList'

# 强制直连：绕过环境注入的不稳定系统代理（127.0.0.1:11719 间歇拒绝连接）
PROXIES = {'http': None, 'https': None}

SOURCES = [
    {'name': '建设工程-招标计划',        'node_id': 209},
    {'name': '建设工程-招标文件提前公示',  'node_id': 210},
    {'name': '建设工程-招标公告',         'node_id': 58},
    {'name': '建设工程-答疑、澄清',        'node_id': 59},
    {'name': '建设工程-评标结果公示',       'node_id': 208},
    {'name': '建设工程-中标候选人公示',     'node_id': 60},
    {'name': '建设工程-中标信息',          'node_id': 61},
    {'name': '建设工程-项目公告',         'node_id': 107},
    {'name': '建设工程-招投标公开信息',     'node_id': 172},
    {'name': '政府采购-采购公告',          'node_id': 53},
    {'name': '政府采购-答疑、更正公告',     'node_id': 54},
    {'name': '政府采购-中标公告',          'node_id': 115},
    {'name': '政府采购-废标公告',          'node_id': 138},
    {'name': '政府采购-采购需求公示',       'node_id': 160},
]
SOURCE_ORDER = {s['name']: i for i, s in enumerate(SOURCES)}
MEMORY_DIR = 'memory'
os.makedirs(MEMORY_DIR, exist_ok=True)


def _c(t):
    return ' '.join((t or '').split())


# ---------- 数据层 ----------

def fetch_source(src, limit=30):
    try:
        r = requests.post(PAGE_LIST_URL,
            data={'offset': 1, 'limit': limit, 'nodeId': src['node_id']},
            headers={'User-Agent': 'Mozilla/5.0',
                     'Referer': f'{BASE_URL}/subItem/{src["node_id"]}'},
            timeout=20, proxies=PROXIES)
        rows = r.json().get('data', {}).get('rows', [])
        items = []
        for row in rows:
            aid = str(row.get('arab01', '')).strip()
            items.append({
                'key':     f"{src['node_id']}-{aid}" if aid else '',
                'title':   _c(row.get('arab04', '')),
                'date':    _c(row.get('arab32', ''))[:10],
                'pub_at':  _c(row.get('arab32', ''))[:16],
                'source':  src['name'],
                'url':     f'{BASE_URL}/artical/{src["node_id"]}/{aid}' if aid else '',
                'node_id': src['node_id'],
                'aid':     aid,
            })
        return items
    except Exception as e:
        print(f'ERR {src["name"]}: {e}', file=sys.stderr)
        return []


def fetch_winner_detail(p):
    if p.get('node_id') != 61 or not p.get('url'):
        return
    try:
        html = requests.get(p['url'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, proxies=PROXIES).text
        soup = BeautifulSoup(html, 'html.parser')
        for tr in soup.select('table tr'):
            th = tr.select_one('th')
            td = tr.select_one('td')
            if th and td:
                label = th.get_text(strip=True)
                val   = td.get_text(strip=True)
                if label == '中标单位':   p['winner'] = val
                elif label == '中标价':    p['price']  = val
                elif label == '中标日期':  p['win_dt'] = val
    except:
        pass


def load_last():
    f = f'{MEMORY_DIR}/zsjypt_last.json'
    if os.path.exists(f):
        with open(f) as fh:
            d = json.load(fh)
            return d if isinstance(d, list) else []
    return []


def save_current(items):
    with open(f'{MEMORY_DIR}/zsjypt_last.json', 'w') as f:
        json.dump(items, f, ensure_ascii=False)


# ---------- 追踪层 ----------

def load_tracking():
    path = f'{MEMORY_DIR}/zsjypt_tracking.json'
    if os.path.exists(path):
        with open(path) as fh:
            d = json.load(fh)
            return d if isinstance(d, dict) else {'terms': {}}
    return {'terms': {}}


def save_tracking(state):
    with open(f'{MEMORY_DIR}/zsjypt_tracking.json', 'w') as fh:
        json.dump(state, fh, ensure_ascii=False)


def add_track(term, all_projects):
    term = _c(term)
    if not term:
        return False
    state = load_tracking()
    terms = state.setdefault('terms', {})
    if term in terms:
        return True
    seen = []
    for p in all_projects:
        if term in (p.get('title') or ''):
            seen.append(p.get('key', ''))
    terms[term] = {'seen': sorted(list(set(seen))) if seen else []}
    save_tracking(state)
    return True


def remove_track(term):
    term = _c(term)
    state = load_tracking()
    terms = state.get('terms', {})
    if term in terms:
        del terms[term]
        save_tracking(state)
    return True


def list_tracks():
    state = load_tracking()
    terms = state.get('terms', {})
    return sorted(terms.keys())


def check_updates(all_projects):
    """检查关注项目是否有新内容"""
    state = load_tracking()
    terms = state.get('terms', {})
    if not terms:
        return {}

    updates = {}
    for term, meta in terms.items():
        seen_keys = set((meta or {}).get('seen', []))
        matched = [p for p in all_projects
                   if term in (p.get('title') or '')
                   and p.get('key', '') not in seen_keys]
        if matched:
            updates[term] = matched
            for p in matched:
                k = p.get('key', '')
                if k:
                    seen_keys.add(k)
            terms[term] = {'seen': sorted(seen_keys)}

    if updates:
        save_tracking(state)
    return updates


# ---------- 班次 ----------

def get_shift():
    h = datetime.now().hour
    if h < 12:   return '早班 08:30'
    elif h < 18: return '午班 12:00'
    else:        return '晚班 18:00'


# ---------- 报告生成 ----------

def make_report(today_items, tracked_updates, shift):
    today = datetime.now().strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = []
    lines.append(f'**中山平台监测汇报（{shift}）**')
    lines.append(f'时间：{now_str}')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append(f'**一、{today} 新挂网清单**')

    if not today_items:
        lines.append('')
        lines.append('本次未发现新增。')
    else:
        grouped = {}
        for p in today_items:
            grouped.setdefault(p['source'], []).append(p)
        total = 0
        for src in sorted(grouped.keys(), key=lambda x: SOURCE_ORDER.get(x, 999)):
            items = grouped[src]
            items.sort(key=lambda x: x.get('pub_at', ''), reverse=True)
            total += len(items)
            lines.append('')
            lines.append(f'**【{src}】** {len(items)} 条')
            for i, p in enumerate(items, 1):
                title = p['title']
                lines.append(f'{i}. {title}')
                extra = []
                if p.get('winner'): extra.append(f'👷 中标单位：{p["winner"]}')
                if p.get('price'):  extra.append(f'💰 中标价：{p["price"]}')
                if extra: lines.append('   ' + ' | '.join(extra))
                link = f'发布：{p["pub_at"]} | [查看]({p["url"]})' if p['url'] else f'发布：{p["pub_at"]}'
                lines.append(f'   {link}')
        lines.append('')
        lines.append(f'📊 共 **{total}条** 新增')

    # 关注项目更新
    if tracked_updates:
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append('**二、关注项目更新**')
        for term in sorted(tracked_updates.keys()):
            items = tracked_updates[term]
            items.sort(key=lambda x: x.get('pub_at', ''), reverse=True)
            lines.append('')
            lines.append(f'**【{term}】** 新增 {len(items)} 条')
            for i, p in enumerate(items, 1):
                title = p['title']
                lines.append(f'{i}. {title}')
                extra = []
                if p.get('winner'): extra.append(f'👷 中标单位：{p["winner"]}')
                if p.get('price'):  extra.append(f'💰 中标价：{p["price"]}')
                if extra: lines.append('   ' + ' | '.join(extra))
                link = f'发布：{p["pub_at"]} | [查看]({p["url"]})' if p['url'] else f'发布：{p["pub_at"]}'
                lines.append(f'   {link}')

    return '\n'.join(lines)


# ---------- 主入口 ----------

def main():
    # 切到脚本目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    args = sys.argv[1:]

    # 抓全量数据（track/untrack/list也需要）
    all_projects = []
    for src in SOURCES:
        all_projects.extend(fetch_source(src))

    # 子命令
    if args:
        cmd = args[0].strip().lower()
        if cmd in ('track', '-t') and len(args) >= 2:
            term = _c(' '.join(args[1:]))
            ok = add_track(term, all_projects)
            print(f'{"已加入关注" if ok else "失败"}：{term}' if term else '关键词不能为空')
            return
        if cmd in ('untrack', '-u') and len(args) >= 2:
            term = _c(' '.join(args[1:]))
            remove_track(term)
            print(f'已移除关注：{term}')
            return
        if cmd in ('list', '-l', 'list-tracked'):
            terms = list_tracks()
            if not terms:
                print('当前没有关注项目。')
            else:
                print(f'当前关注项目（{len(terms)} 个）：')
                for t in terms:
                    print(f'  · {t}')
            return
        print(__doc__)

    today = datetime.now().strftime('%Y-%m-%d')
    today_items = [p for p in all_projects if p['date'] == today]

    # 抓中标详情（对所有中标信息条目持久化：优先复用历史快照，避免重复抓取）
    prev_map = {p.get('key'): p for p in load_last() if isinstance(p, dict)}
    for p in all_projects:
        if p.get('node_id') == 61 and not p.get('winner'):
            old = prev_map.get(p.get('key'))
            if old and old.get('winner'):
                p['winner'] = old['winner']
                p['price'] = old.get('price', '')
                p['win_dt'] = old.get('win_dt', '')
            else:
                fetch_winner_detail(p)

    # 检查关注更新
    tracked_updates = check_updates(all_projects)
    for term, items in tracked_updates.items():
        for p in items:
            if p['node_id'] == 61:
                fetch_winner_detail(p)

    shift = get_shift()
    report = make_report(today_items, tracked_updates, shift)
    print(report)

    # 更新last-check（仅当抓取到数据时保存，防止全部栏目失败时把历史基线快照覆盖成空）
    if all_projects:
        save_current(all_projects)
    else:
        print('⚠ 全部栏目抓取失败，已保留上一份快照（zsjypt_last.json 未覆盖），本次报告不可信')

    # 多平台推送（可选）：有配置才推，失败不影响主流程
    try:
        import notify
        if notify.is_configured():
            for r in notify.push(report, f'中山平台监测（{shift}）'):
                print('PUSH ' + r)
    except Exception as e:
        print('PUSH-SKIP ' + str(e))

    return report


if __name__ == '__main__':
    main()
