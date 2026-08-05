# 多平台推送（飞书 / 企业微信 / 钉钉）

本 skill 支持把每日报告推送到群机器人。微信个人号无官方推送接口，统一走**企业微信群机器人**（即推到微信）。

## 首次配置引导

首次加载或后续需增配推送时，主动弹出配置引导（不要静默跳过）：

```bash
cd <repo>/scripts
python notify.py --guide     # 弹出配置引导：说明三个平台如何获取 Webhook
```

引导涵盖：飞书 / 企业微信 / 钉钉各自的 Webhook 获取路径、加签 secret 填写、以及 `config/notify.json` 与环境变量两种配置方式。

## 配置模板

```json
{
  "feishu":   { "webhook": "（填飞书自定义机器人 Webhook）", "secret": "" },
  "wecom":    { "webhook": "（填企业微信群机器人 Webhook，即推到微信）", "secret": "" },
  "dingtalk": { "webhook": "（填钉钉自定义机器人 Webhook）", "secret": "" }
}
```

- 三个平台各留一个 Webhook 占位符（非 http 开头即视为未配置）。用户**只需把对应地址填进去，无需改任何逻辑**——脚本自动按平台拼装报文并推送，未填的平台自动跳过。
- 支持环境变量覆盖：`ZS_NOTIFY_FEISHU` / `ZS_NOTIFY_WECOM` / `ZS_NOTIFY_DINGTALK`。
- 飞书 / 钉钉开启「加签」时填 `secret`。

## 验证与试用

```bash
python notify.py --status    # 看已启用哪些平台
python notify.py --test      # 发一条测试消息
```

## 自动推送

- `crab-monitor.py` 末尾在生成报告后自动推送至 `config/notify.json` 中已配置的飞书/企业微信/钉钉；未配置则跳过，不影响主流程。
- `is_configured()` 判定任一平台填了有效（http 开头）webhook 即为已配置。
- 密钥绝不打印：校验/状态输出只报「平台是否已启用」，绝不输出 webhook 值与 secret。
