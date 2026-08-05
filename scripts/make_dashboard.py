#!/usr/bin/env python3
"""
中山平台监测 - 可视化仪表盘生成器（常驻面板模式）

设计：
  - dashboard.html 是固定外壳（只写一次，架构不变），内含 JS 渲染逻辑
  - 每次抓取只更新 dashboard-data.js（纯数据），面板读它渲染
  - 因此 HTML 不被重新生成，新清单直接"接入"面板

用法：
  python make_dashboard.py                 # 更新 reports/live/ 的 data.js（外壳缺失时一并创建）
  python make_dashboard.py --standalone    # 额外生成一份自包含的单文件 HTML（用于分享/预览）
  python make_dashboard.py --rebuild       # 强制重建 dashboard.html 外壳（模板更新后同步用）
  python make_dashboard.py 2026-07-29       # 指定日期（默认今天）
"""
import os, sys, json
from datetime import datetime
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.normpath(os.path.join(HERE, '..', 'reports'))
LIVE_DIR = os.path.join(REPORTS_DIR, 'live')

SHELL_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>中山平台监测 · 仪表盘</title>
<style>
:root{--bg:#f5f7fa;--card:#fff;--ink:#1f2933;--sub:#6b7785;--line:#e4e9f0;
      --accent:#2563eb;--green:#16a34a;--amber:#d97706;--bar:#3b82f6;--bar2:#93c5fd;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
     background:var(--bg);color:var(--ink);padding:28px;line-height:1.5}
.wrap{max-width:1040px;margin:0 auto}
header{display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:22px}
h1{font-size:24px;font-weight:700}
.meta{color:var(--sub);font-size:14px}
.shift{display:inline-block;background:var(--accent);color:#fff;border-radius:6px;padding:2px 10px;font-size:13px;margin-left:8px;vertical-align:middle}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.kpi .num{font-size:34px;font-weight:800;color:var(--accent);line-height:1}
.kpi .lbl{color:var(--sub);font-size:13px;margin-top:6px}
.kpi.alt .num{color:var(--green)}
.kpi.warn .num{color:var(--amber)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px;margin-bottom:22px}
.panel h2{font-size:16px;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.panel h2::before{content:"";width:4px;height:16px;background:var(--accent);border-radius:2px;display:inline-block}
.bars{display:flex;flex-direction:column;gap:11px}
.row{display:grid;grid-template-columns:170px 1fr 34px;align-items:center;gap:12px;font-size:14px}
.row .name{color:var(--sub);text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.track{background:#eef2f7;border-radius:6px;height:18px;overflow:hidden}
.track>span{display:block;height:100%;background:linear-gradient(90deg,var(--bar),var(--bar2));border-radius:6px}
.row .val{font-weight:700;text-align:left}
.group{margin-bottom:18px}
.group:last-child{margin-bottom:0}
.ghead{font-size:14px;font-weight:700;color:var(--accent);margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.ghead .cnt{background:#eef2f7;color:var(--sub);border-radius:20px;padding:1px 10px;font-size:12px;font-weight:600}
.items{display:flex;flex-direction:column;gap:9px}
.item{background:#fafbfc;border:1px solid var(--line);border-radius:9px;padding:12px 14px;transition:.15s}
.item:hover{border-color:var(--bar2);box-shadow:0 2px 10px rgba(37,99,235,.08)}
.item .t{font-weight:600;font-size:14.5px}
.item .t a{color:inherit;text-decoration:none}
.item .t a:hover{color:var(--accent);text-decoration:underline}
.item .b{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px;font-size:12.5px;color:var(--sub)}
.tag{background:#eef6ff;color:var(--accent);border-radius:5px;padding:1px 8px;font-weight:600}
.win{background:#ecfdf3;color:var(--green);border-radius:5px;padding:1px 8px;font-weight:600}
.price{background:#fff7ed;color:var(--amber);border-radius:5px;padding:1px 8px;font-weight:600}
.track-sec{display:flex;flex-wrap:wrap;gap:10px}
.chip{display:flex;align-items:center;gap:8px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:30px;padding:7px 14px;font-size:13.5px;font-weight:600;color:#166534}
.chip.warn{background:#fffbeb;border-color:#fde68a;color:#92400e}
.dot{width:9px;height:9px;border-radius:50%;background:var(--green)}
.dotw{width:9px;height:9px;border-radius:50%;background:var(--amber)}
.foot{color:var(--sub);font-size:12px;text-align:center;margin-top:8px}
.empty{color:var(--sub);text-align:center;padding:30px 0}
@media(max-width:640px){.kpis{grid-template-columns:1fr}.row{grid-template-columns:110px 1fr 28px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div><h1>中山市公共资源交易平台监测 <span class="shift" id="shift"></span></h1>
    <div class="meta" id="meta"></div></div>
  </header>
  <div class="kpis" id="kpis"></div>
  <div class="panel"><h2>栏目分布</h2><div class="bars" id="bars"></div></div>
  <div class="panel"><h2>今日新挂网清单</h2><div id="groups"></div></div>
  <div class="panel"><h2>关注公司追踪</h2><div class="track-sec" id="tracking"></div></div>
  <div class="foot" id="foot"></div>
</div>
<script src="dashboard-data.js"></script>
<script>
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function render(d){
  if(!d||d.error){document.getElementById('meta').textContent='数据未加载（请确认 dashboard-data.js 与本页面同目录）';return;}
  document.getElementById('shift').textContent=d.shift||'';
  document.getElementById('meta').textContent=d.date+' · 数据来源 zsjypt.cn · '+d.scope;
  document.getElementById('foot').textContent='由 crab-monitor.py + make_dashboard.py 生成 · 自动化定时（工作日 12:00 / 18:00）· '+d.push;
  var k=document.getElementById('kpis');
  k.innerHTML=
    '<div class="kpi"><div class="num">'+d.total+'</div><div class="lbl">今日新增项目</div></div>'+
    '<div class="kpi alt"><div class="num">'+d.cats+'</div><div class="lbl">涉及栏目数</div></div>'+
    '<div class="kpi'+(d.track_new?' warn':'')+'"><div class="num">'+d.track_new+'</div><div class="lbl">追踪公司新增</div></div>';
  var bars=document.getElementById('bars');
  if(d.bars&&d.bars.length){
    bars.innerHTML=d.bars.map(function(b){
      var w=Math.max(38,Math.round(b.cnt/d.maxcnt*100));
      return '<div class="row"><div class="name">'+esc(b.name)+'</div>'+
             '<div class="track"><span style="width:'+w+'%"></span></div>'+
             '<div class="val">'+b.cnt+'</div></div>';
    }).join('');
  } else bars.innerHTML='<div class="empty">本次未发现新增。</div>';
  var g=document.getElementById('groups');
  if(d.groups&&d.groups.length){
    g.innerHTML=d.groups.map(function(grp){
      var cards=grp.items.map(function(p){
        var link=p.url?('<a href="'+esc(p.url)+'" target="_blank">'+esc(p.title)+'</a>'):esc(p.title);
        var b='<span class="tag">发布 '+(p.pub?p.pub.slice(-5):'')+'</span>';
        if(p.aid)b+='<span>ID '+esc(p.aid)+'</span>';
        if(p.winner)b+='<span class="win">👷 中标单位：'+esc(p.winner)+'</span>';
        if(p.price)b+='<span class="price">💰 中标价：'+esc(p.price)+'</span>';
        return '<div class="item"><div class="t">'+link+'</div><div class="b">'+b+'</div></div>';
      }).join('');
      return '<div class="group"><div class="ghead"><span>'+esc(grp.src)+'</span>'+
             '<span class="cnt">'+grp.items.length+'</span></div><div class="items">'+cards+'</div></div>';
    }).join('');
  } else g.innerHTML='<div class="empty">本次未发现新增。</div>';
  var t=document.getElementById('tracking');
  if(d.tracking&&d.tracking.length){
    t.innerHTML=d.tracking.map(function(x){
      if(x.cnt>0)return '<div class="chip warn"><span class="dotw"></span>'+esc(x.term)+' · 今日 '+x.cnt+' 条更新</div>';
      return '<div class="chip"><span class="dot"></span>'+esc(x.term)+' · 今日无更新</div>';
    }).join('');
  } else t.innerHTML='<div class="empty">未配置追踪关键词。</div>';
}
render(window.DASHBOARD_DATA);
</script>
</body>
</html>'''


def load_cm():
    spec = importlib.util.spec_from_file_location('cm', os.path.join(HERE, 'crab-monitor.py'))
    cm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cm)
    return cm


def get_shift():
    h = datetime.now().hour
    if h < 12:
        return '早班 08:30'
    elif h < 18:
        return '午班 12:00'
    return '晚班 18:00'


def _push_status():
    """探测已启用的推送平台（飞书/企业微信/钉钉），返回展示文案。"""
    try:
        import notify as _notify
        cfg = _notify.load_config()
        names = {'feishu': '飞书', 'wecom': '企业微信', 'dingtalk': '钉钉'}
        enabled = [names.get(n, n) for n in _notify.PLATFORMS
                   if str(cfg.get(n, {}).get('webhook', '')).lower().startswith('http')]
        if enabled:
            return '推送：' + '/'.join(enabled)
    except Exception:
        pass
    return '推送未配置'


def build_data(date_str, cm):
    all_projects = cm.load_last()
    if not all_projects:
        all_projects = []
        for src in cm.SOURCES:
            all_projects.extend(cm.fetch_source(src))

    # 全量当日条目：用于追踪统计（追踪与关键词过滤相互独立）
    today_all = [p for p in all_projects if p.get('date') == date_str]

    # 用户私有过滤项：与 crab-monitor.py 的 init 配置保持一致
    user_cfg = cm.load_user_config()
    keywords = user_cfg.get('keywords', []) or []
    if keywords:
        today_items = [p for p in today_all
                       if any(k in (p.get('title') or '') for k in keywords)]
        scope = '已按关键词过滤：' + '/'.join(keywords)
    else:
        today_items = today_all
        scope = '全量监控（未设置关键词过滤）'

    grouped = {}
    for p in today_items:
        grouped.setdefault(p['source'], []).append(p)

    groups = []
    for src in sorted(grouped.keys(), key=lambda x: cm.SOURCE_ORDER.get(x, 999)):
        items = sorted(grouped[src], key=lambda x: x.get('pub_at', ''), reverse=True)
        groups.append({'src': src, 'items': [{
            'title': p.get('title', ''),
            'url': p.get('url', ''),
            'pub': p.get('pub_at', '') or p.get('date', ''),
            'aid': p.get('aid', ''),
            'winner': p.get('winner', ''),
            'price': p.get('price', ''),
        } for p in items]})

    counts = [(src, len(grouped.get(src, []))) for src in
              sorted(grouped.keys(), key=lambda x: cm.SOURCE_ORDER.get(x, 999))]
    maxcnt = max([c for _, c in counts], default=1) or 1
    bars = [{'name': n, 'cnt': c} for n, c in counts]

    tracking = cm.load_tracking().get('terms', {})
    track_list = [{'term': t, 'cnt': sum(1 for p in today_all if t in (p.get('title') or ''))}
                  for t in sorted(tracking.keys())]

    return {
        'date': date_str,
        'shift': get_shift(),
        'scope': scope,
        'push': _push_status(),
        'keywords': keywords,
        'total': len(today_items),
        'cats': len(grouped),
        'track_new': sum(x['cnt'] for x in track_list),
        'maxcnt': maxcnt,
        'bars': bars,
        'groups': groups,
        'tracking': track_list,
    }


def main():
    os.chdir(HERE)
    cm = load_cm()
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    date_str = args[0] if args else datetime.now().strftime('%Y-%m-%d')
    standalone = '--standalone' in sys.argv
    rebuild = '--rebuild' in sys.argv

    data = build_data(date_str, cm)

    os.makedirs(LIVE_DIR, exist_ok=True)
    # 只更新数据文件（面板外壳不变）
    with open(os.path.join(LIVE_DIR, 'dashboard-data.js'), 'w', encoding='utf-8') as f:
        f.write('window.DASHBOARD_DATA = ' + json.dumps(data, ensure_ascii=False) + ';')
    # 外壳仅缺时创建；--rebuild 时强制重建（用于外壳模板更新后同步）
    shell_path = os.path.join(LIVE_DIR, 'dashboard.html')
    if rebuild or not os.path.exists(shell_path):
        with open(shell_path, 'w', encoding='utf-8') as f:
            f.write(SHELL_HTML)

    print('LIVE ' + os.path.join(LIVE_DIR, 'dashboard-data.js'))

    # 可选：生成自包含单文件 HTML（用于分享/预览，数据内联）
    if standalone:
        out_dir = os.path.join(REPORTS_DIR, date_str)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'dashboard.html')
        html = SHELL_HTML.replace('<script src="dashboard-data.js"></script>',
                                  '<script>window.DASHBOARD_DATA = ' + json.dumps(data, ensure_ascii=False) + ';</script>')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print('STANDALONE ' + out_path)


if __name__ == '__main__':
    main()
