"""
Notification Module (v5.0)
===========================
Dispatches daily Master Alpha reports, The Pre-Breakout Elite 5,
and Institutional F&O Radar directly to Telegram and Discord.
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

def format_elite_five_alert(elite_five_df, regime, regime_metrics, today_display, fno_radar_df=None):
    """
    Formats a concise, high-impact alert text suitable for mobile notifications
    highlighting Pre-Breakout Coils and F&O Radar.
    """
    lines = [
        f"🏛️ *NSE ALPHA ENGINE v5.0 — {today_display}*",
        f"📊 *Market Regime:* `{regime}` ({regime_metrics['position_size_pct']}% Sizing)",
        "",
        "💎 *THE PRE-BREAKOUT ELITE 5 (COILED SPRINGS):*",
        "> *Catching moves BEFORE breakout — Low-Risk Launchpads*",
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
            fno_tag = " `[F&O]`" if r.get('is_fno') else ""
            dist = r.get('dist_to_pivot_pct', 0.0)
            
            lines.append(f"*{idx+1}. {sym}*{fno_tag} ({sec})")
            lines.append(f"   • Setup: `{pat}` | Score: `{score:.1f}`")
            lines.append(f"   • Close: `₹{entry:.1f}` | Pivot Dist: `{dist:+.1f}%`")
            lines.append(f"   • Tight Stop: `₹{stop:.1f}` | Target: `1:4+ R/R`")
            lines.append("")
    else:
        lines.append("⚠️ *No candidates passed 100% strict pre-breakout convergence today.*")
        lines.append("")
        
    if fno_radar_df is not None and not fno_radar_df.empty:
        lines.extend([
            "━━━━━━━━━━━━━━━━━━━━",
            "⚡ *INSTITUTIONAL F&O SQUEEZE RADAR:*",
            "> *Top Derivatives Coils (Futures / Call Options)*"
        ])
        for idx, r in fno_radar_df.head(3).iterrows():
            sym = r['symbol']
            pat = r['pattern']
            entry = r['close']
            dist = r.get('dist_to_pivot_pct', 0.0)
            score = r['alpha_score']
            lines.append(f"• *{sym}*: `{pat}` | ₹{entry:.1f} (Dist: `{dist:+.1f}%`) | Score: `{score:.1f}`")
        lines.append("")
        
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("🛡️ *Rule:* Never buy extended > +4% | Max 1% Risk | Chandelier Stops Active.")
    return "\n".join(lines)
