#!/usr/bin/env python3
"""
中山平台监测 · 多平台推送模块（飞书 / 企业微信 / 钉钉）

设计要点
--------
- 零依赖：仅用标准库（urllib / hmac / hashlib），与 crab-monitor.py 同一 venv 即可。
- 自动适配：只要在 config/notify.json（或环境变量）里把某平台的 webhook 填上，
  就自动推送该平台；留空 / 占位符则跳过。**无需改动任何逻辑**。
- 微信个人号无官方推送接口，故「推到微信」统一走企业微信群机器人（wecom）。
- 安全：推送失败只记录，绝不影响主监控流程。

用法
----
  python notify.py --guide     # 弹出配置引导（首次加载 / 后续增配时）
  python notify.py --status    # 查看当前已启用哪些平台
  python notify.py --test      # 发一条测试消息（验证 webhook 是否可用）
  python notify.py             # 等同 --status

在 crab-monitor.py 中调用（可选）：
  import notify
  if notify.is_configured():
      notify.push(report_text, title='中山平台监测（晚班 18:00）')
"""
import os
import sys
import json
import time
import base64
import hmac
import hashlib
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.normpath(os.path.join(HERE, '..', 'config', 'notify.json'))

# 三个平台。占位符一律不以 http 开头 → is_configured() 自动判定为"未配置"。
DEFAULT_CONFIG = {
    "feishu": {
        "webhook": "（请填入飞书自定义机器人 Webhook，形如 https://open.feishu.cn/open-apis/bot/v2/hook/xxxx）",
        "secret": "",
    },
    "wecom": {
        "webhook": "（请填入企业微信群机器人 Webhook，即「推到微信」，形如 https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx）",
        "secret": "",
    },
    "dingtalk": {
        "webhook": "（请填入钉钉自定义机器人 Webhook，形如 https://oapi.dingtalk.com/robot/send?access_token=xxxx）",
        "secret": "",
    },
    "note": "把对应平台 webhook 替换为真实地址即可启用推送；留空或保留占位符则自动跳过该平台。钉钉/飞书开启加签时填 secret。也可用环境变量 ZS_NOTIFY_FEISHU / ZS_NOTIFY_WECOM / ZS_NOTIFY_DINGTALK 覆盖。",
}

PLATFORMS = ('feishu', 'wecom', 'dingtalk')


def load_config():
    """读取 config/notify.json，并用环境变量覆盖。占位符（非 http 开头）保持原样。"""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝默认
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                user = json.load(f)
            for k in PLATFORMS:
                if isinstance(user.get(k), dict):
                    cfg[k]['webhook'] = user[k].get('webhook', cfg[k]['webhook'])
                    cfg[k]['secret'] = user[k].get('secret', cfg[k]['secret'])
        except Exception:
            pass
    # 环境变量覆盖（最高优先级）
    env_map = {'feishu': 'ZS_NOTIFY_FEISHU', 'wecom': 'ZS_NOTIFY_WECOM', 'dingtalk': 'ZS_NOTIFY_DINGTALK'}
    for k, env in env_map.items():
        v = os.environ.get(env)
        if v:
            cfg[k]['webhook'] = v
    return cfg


def _is_valid(url):
    return isinstance(url, str) and url.strip().lower().startswith('http')


def _post(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, data=data, headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode('utf-8', 'ignore')


# ---------- 各平台适配器（报文格式自动适配）----------

def _feishu_sign(secret):
    ts = str(int(time.time()))
    string_to_sign = ts + '\n' + secret
    hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
    return ts, base64.b64encode(hmac_code).decode('utf-8')


def push_feishu(webhook, secret, text):
    url = webhook
    if secret:
        ts, sign = _feishu_sign(secret)
        sep = '&' if '?' in url else '?'
        url = f"{url}{sep}timestamp={ts}&sign={urllib.parse.quote(sign)}"
    payload = {"msg_type": "text", "content": {"text": text[:4000]}}
    return _post(url, payload)


def push_wecom(webhook, secret, text):
    # 企业微信 text 上限 2048 字节，安全截断到 1900 字符
    content = text[:1900]
    if len(text) > 1900:
        content += "\n…（内容过长已截断，完整见仪表盘）"
    payload = {"msgtype": "text", "text": {"content": content}}
    return _post(webhook, payload)


def push_dingtalk(webhook, secret, text):
    url = webhook
    if secret:
        ts = str(round(time.time() * 1000))
        string_to_sign = f"{ts}\n{secret}"
        hmac_code = hmac.new(secret.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote(base64.b64encode(hmac_code).decode('utf-8'))
        sep = '&' if '?' in url else '?'
        url = f"{url}{sep}timestamp={ts}&sign={sign}"
    payload = {"msgtype": "text", "text": {"content": text[:4000]}}
    return _post(url, payload)


ADAPTERS = {
    'feishu': push_feishu,
    'wecom': push_wecom,
    'dingtalk': push_dingtalk,
}


def is_configured():
    """任一平台填了有效（http 开头）webhook 即为已配置。"""
    cfg = load_config()
    return any(_is_valid(cfg[k].get('webhook')) for k in PLATFORMS)


def push(text, title=''):
    """推送正文到所有已配置平台。返回结果列表，例如 ['feishu: OK', 'dingtalk: FAIL ...']。"""
    cfg = load_config()
    body = f"{title}\n\n{text}" if title else text
    results = []
    for name in PLATFORMS:
        wh = cfg[name].get('webhook', '')
        if not _is_valid(wh):
            continue
        try:
            ADAPTERS[name](wh, cfg[name].get('secret', ''), body)
            results.append(f'{name}: OK')
        except Exception as e:
            results.append(f'{name}: FAIL {type(e).__name__}: {e}')
    return results


# ---------- 配置引导提示 ----------

CONFIG_GUIDE = """\
================================================================
  中山平台监测 · 多平台推送配置引导
================================================================
支持把每日监测报告推送到以下群聊机器人（只需填 webhook，自动适配，无需改代码）：
  • 飞书 (Feishu / Lark)
  • 企业微信 (WeCom) ——「推到微信」即走企业微信群机器人
  • 钉钉 (DingTalk)

【说明】微信个人号没有官方推送接口，因此「推到微信」统一用企业微信群机器人实现。

----------------------------------------------------------------
配置方式（任选其一）
----------------------------------------------------------------
方式 A · 编辑 config/notify.json
  把对应平台的 "webhook" 换成真实机器人地址；不用的平台保留占位符或留空 "" 即自动跳过。
  钉钉 / 飞书若开启了「加签」，把密钥填入同项的 "secret"。

方式 B · 环境变量（临时 / 命令行优先）
  ZS_NOTIFY_FEISHU=https://open.feishu.cn/...
  ZS_NOTIFY_WECOM=https://qyapi.weixin.qq.com/...
  ZS_NOTIFY_DINGTALK=https://oapi.dingtalk.com/...

----------------------------------------------------------------
各平台如何获取 Webhook
----------------------------------------------------------------
1) 飞书
   群聊 → 设置 → 群机器人 → 添加机器人 → 自定义机器人
   → 复制 Webhook（形如 https://open.feishu.cn/open-apis/bot/v2/hook/xxxx）
   → 若开启「签名校验」，复制 secret 填到 notify.json 的 feishu.secret

2) 企业微信（即微信推送）
   群聊 → 右上角 ··· → 添加群机器人 → 新建一个机器人
   → 复制 Webhook（形如 https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx）
   → 企业微信机器人免签名，secret 留空即可

3) 钉钉
   群聊 → 智能群助手 → 添加机器人 → 自定义(通过 Webhook 接入)
   → 复制 Webhook（形如 https://oapi.dingtalk.com/robot/send?access_token=xxxx）
   → 若开启「加签」，复制密钥填到 notify.json 的 dingtalk.secret

----------------------------------------------------------------
配置后验证
----------------------------------------------------------------
  python scripts/notify.py --status    # 查看已启用哪些平台
  python scripts/notify.py --test       # 发送一条测试消息
  python scripts/notify.py --guide      # 随时重新弹出本引导（首配 / 增配）

填好地址后，自动化（工作日 12:00 / 18:00）跑完会自动把报告推到已配置的平台。
================================================================"""


def show_guide():
    print(CONFIG_GUIDE)


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else '--status'
    if arg in ('--guide', '-g', 'guide'):
        show_guide()
        return
    if arg in ('--test', '-t', 'test'):
        if not is_configured():
            print('尚未配置任何平台 webhook。先运行：python scripts/notify.py --guide')
            return
        res = push('✅ 中山平台监测推送测试消息（来自 notify.py）', title='推送测试')
        for r in res:
            print('PUSH ' + r)
        return
    # 默认 / --status
    cfg = load_config()
    print('多平台推送配置状态：')
    for name in PLATFORMS:
        wh = cfg[name].get('webhook', '')
        if _is_valid(wh):
            print(f'  ✅ {name:8s} 已配置')
        else:
            print(f'  ⬜ {name:8s} 未配置（占位符/空）')
    if not is_configured():
        print('\n未启用任何推送。运行 `python scripts/notify.py --guide` 查看配置方法。')


if __name__ == '__main__':
    main()
