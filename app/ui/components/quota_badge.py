import streamlit as st
from app.core.constants import BADGES


def quota_badge(risk_level: str) -> str:
    colors = {
        "low": "#2e7d32",
        "medium": "#e8710a",
        "high": "#d32f2f",
        "blocked": "#b71c1c",
    }
    labels = {
        "low": BADGES["safe"],
        "medium": BADGES["low_quota"],
        "high": BADGES["nearly_exhausted"],
        "blocked": BADGES["blocked"],
    }
    color = colors.get(risk_level, "#9e9e9e")
    label = labels.get(risk_level, risk_level)
    return f'<span style="background:{color};padding:2px 10px;border-radius:10px;color:white;font-size:0.75em;font-weight:bold">{label}</span>'


def reset_badge(reset_policy: str) -> str:
    badges = {
        "monthly_billing_cycle": ("RESET MENSAL", "#1a73e8"),
        "daily_rate_limit": ("RESET DIÁRIO", "#e8710a"),
        "one_time_trial_credit": ("CRÉDITO INICIAL", "#9c27b0"),
        "manual_balance": ("MANUAL", "#607d8b"),
        "paid_topup": ("TOP-UP", "#ff9800"),
        "pay_as_you_go": ("PAGO", "#d32f2f"),
        "unknown": ("INCERTO", "#f44336"),
    }
    label, color = badges.get(reset_policy, (reset_policy.replace("_", " ").upper(), "#9e9e9e"))
    return f'<span style="background:{color};padding:2px 10px;border-radius:10px;color:white;font-size:0.75em;font-weight:bold">{label}</span>'


def fallback_timeline(fallback_chain: list[str]) -> str:
    if not fallback_chain:
        return ""
    html = '<div style="font-size:0.85em;margin:8px 0">'
    html += "Fallback: "
    for i, provider in enumerate(fallback_chain):
        html += f'<span style="background:#d32f2f;padding:1px 8px;border-radius:8px;color:white;margin:0 2px">{provider}</span>'
        if i < len(fallback_chain):
            html += " → "
    html += "</div>"
    return html


def warning_box(message: str, level: str = "warning") -> str:
    icons = {"warning": "⚠️", "error": "🚫", "info": "ℹ️", "success": "✅"}
    icon = icons.get(level, "ℹ️")
    colors = {"warning": "#fff3e0", "error": "#ffebee", "info": "#e3f2fd", "success": "#e8f5e9"}
    border = {"warning": "#ff9800", "error": "#f44336", "info": "#2196f3", "success": "#4caf50"}
    bg = colors.get(level, "#f5f5f5")
    bc = border.get(level, "#9e9e9e")
    return f'<div style="background:{bg};border-left:4px solid {bc};padding:8px 12px;margin:8px 0;border-radius:4px">{icon} {message}</div>'
