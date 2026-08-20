"""
Notification Module
===================
Dispatches daily Master Alpha reports and The Elite 5 directly to Telegram or Discord webhooks.
"""

import os
import requests
import json
from datetime import datetime

def send_telegram_alert(message_text, bot_token=None, chat_id=None):
    """
    Sends message to Telegram via Bot API.
    """
    token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat:
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"  [Warn] Telegram alert failed: {e}")
        return False

def send_discord_alert(message_text, webhook_url=None):
    """
    Sends formatted message to Discord webhook.
    """
    url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return False
        
    payload = {
        "content": message_text
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 204
    except Exception as e:
        print(f"  [Warn] Discord alert failed: {e}")
        return False

def format_elite_five_alert(elite_five_df, regime, regime_metrics, today_display):
    """
    Formats a concise, high-impact alert text suitable for mobile notifications.
    """
    lines = [
        f"🏛️ *NSE ALPHA ENGINE v4.5 — {today_display}*",
        f"📊 *Market Regime:* `{regime}` ({regime_metrics['position_size_pct']}% Sizing)",
        "",
        "💎 *TODAY'S ELITE 5 (RIPE TO BUY):*",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    
    if not elite_five_df.empty:
        for idx, r in elite_five_df.iterrows():
            sym = r['symbol']
            sec = r['sector']
            pat = r['pattern']
            entry = r['close']
            stop = r['stop_loss']
            score = r['alpha_score']
            
            lines.append(f"*{idx+1}. {sym}* ({sec})")
            lines.append(f"   • Setup: `{pat}` | Score: `{score:.1f}`")
            lines.append(f"   • Entry: `₹{entry:.1f}` | Stop: `₹{stop:.1f}`")
            lines.append(f"   • Target: `1:4+ R/R`")
            lines.append("")
    else:
        lines.append("⚠️ *No candidates passed 100% strict convergence today.*")
        lines.append("")
        
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🛡️ *Rule:* Max 1.0% Account Risk per position | Chandelier ATR Trailing Stops active.")
    return "\n".join(lines)
