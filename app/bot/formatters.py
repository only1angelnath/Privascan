"""
Day 10 — Telegram message formatters.
All output is MarkdownV2 — special chars must be escaped.
Visual style matches the system design spec exactly.
"""

from __future__ import annotations
import re


# ── MarkdownV2 escaper ────────────────────────────────────────────────────────
_MD_SPECIAL = r"\_*[]()~`>#+-=|{}.!"

def esc(text: str) -> str:
    """Escape all MarkdownV2 special characters."""
    return re.sub(r"([\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])", r"\\\1", str(text))


# ── Grade helpers ──────────────────────────────────────────────────────────────
GRADE_EMOJI = {
    "A": "🟢", "B": "🟩", "C": "🟡",
    "D": "🟠", "F": "🔴",
}
OVERRIDE_EMOJI = {
    "ofac_active":     "⛔",
    "exploit_active":  "💀",
    "ofac_resolved":   "🔵",
    "exploit_resolved":"🔵",
}
GRADE_LABEL = {
    "A": "Low Risk",
    "B": "Moderate\\-Low Risk",
    "C": "Moderate Risk",
    "D": "High Risk",
    "F": "Critical Risk",
}


def grade_emoji(grade: str, override_status: str | None = None) -> str:
    if override_status in OVERRIDE_EMOJI:
        return OVERRIDE_EMOJI[override_status]
    return GRADE_EMOJI.get(grade, "⚪")


def progress_bar(score: float, width: int = 10) -> str:
    """█████░░░░░  65/100"""
    filled = round((score / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar}  {int(score)}/100"


# ── Score result message ───────────────────────────────────────────────────────
def format_scan_result(result: dict) -> str:
    """
    Full scan result message for /scan command.
    Uses MarkdownV2 formatting.
    """
    score    = result.get("composite_score", 0)
    grade    = result.get("grade", "F")
    override = result.get("override_status")
    address  = result.get("address", "")
    chain    = result.get("chain", "")
    label    = result.get("grade_label", GRADE_LABEL.get(grade, "Unknown"))
    sub      = result.get("sub_scores", {})

    emoji = grade_emoji(grade, override)
    short_addr = f"{address[:6]}…{address[-4:]}" if len(address) > 10 else address

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"{emoji} *PRIVASCAN SCAN RESULT*",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"📍 `{esc(address)}`",
        f"🔗 Chain: {esc(chain.capitalize())}",
        "",
    ]

    if override == "ofac_active":
        lines += [
            "⛔ *OFAC SANCTIONED*",
            f"Score: {esc(str(score))}/100 · Grade: F",
            "_This contract is on the OFAC consolidated sanctions list\\._",
        ]
    elif override == "exploit_active":
        lines += [
            "💀 *ACTIVE EXPLOIT*",
            f"Score: {esc(str(score))}/100 · Grade: F",
            "_Unresolved exploit on record\\. Exercise extreme caution\\._",
        ]
    else:
        lines += [
            f"📊 *Score: {esc(str(score))}/100*",
            f"🏷 Grade: *{esc(grade)}* — {esc(label)}",
            "",
            "*Sub\\-scores:*",
            f"  Code Risk    `{progress_bar(sub.get('code', 0))}`",
            f"  Ownership    `{progress_bar(sub.get('ownership', 0))}`",
            f"  Liquidity    `{progress_bar(sub.get('liquidity', 0))}`",
            f"  Audit        `{progress_bar(sub.get('audit', 0))}`",
            f"  Compliance   `{progress_bar(sub.get('compliance', 0))}`",
            f"  Governance   `{progress_bar(sub.get('governance', 0))}`",
        ]

    cached = result.get("cached", False)
    scored_at = result.get("scored_at", "")[:10] if result.get("scored_at") else ""

    lines += [
        "",
        f"🔗 [Full report](https://privascan\\.xyz/score/{esc(chain)}/{esc(address)})",
        f"{'⚡ Cached' if cached else '🔄 Fresh scan'}" + (f" · {esc(scored_at)}" if scored_at else ""),
        "━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)


# ── Protocol list ──────────────────────────────────────────────────────────────
def format_protocol_list(protocols: list[dict]) -> str:
    """
    Compact protocol directory for /protocols command.
    """
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "🔍 *PRIVASCAN PROTOCOL DIRECTORY*",
        f"_{esc(str(len(protocols)))} curated EVM privacy protocols_",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for p in protocols:
        score_data = p.get("latest_score")
        if score_data:
            score = score_data.get("composite_score", 0)
            grade = score_data.get("grade", "?")
            override = score_data.get("override_status")
            emoji = grade_emoji(grade, override)
            score_str = f"{emoji} {int(score)}/100 \\({esc(grade)}\\)"
        else:
            score_str = "⚪ _Not yet scored_"

        slug = p.get("slug", "")
        name = p.get("name", "")
        lines.append(
            f"• *{esc(name)}* — {score_str}\n"
            f"  `/scan` or [privascan\\.xyz/protocol/{esc(slug)}](https://privascan.xyz/protocol/{esc(slug)})"
        )

    lines += [
        "",
        "Use `/scan <chain> <address>` to score any contract\\.",
        "━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    return "\n".join(lines)


# ── Alert message ──────────────────────────────────────────────────────────────
def format_alert(
    address: str,
    chain: str,
    old_score: float,
    new_score: float,
    old_grade: str,
    new_grade: str,
    sub_scores: dict,
    new_flags: list[str] | None = None,
    protocol_name: str | None = None,
    override_status: str | None = None,
) -> str:
    """
    Score change alert. Sent when watchlist threshold is breached.
    """
    delta = new_score - old_score
    delta_str = f"{'+' if delta > 0 else ''}{delta:.1f}"
    direction = "📈" if delta > 0 else "📉"
    emoji = grade_emoji(new_grade, override_status)

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"{emoji} *PRIVASCAN SMART CONTRACT RISK ALERT*",
        "━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    if protocol_name:
        lines.append(f"📋 Protocol: *{esc(protocol_name)}*")

    lines += [
        f"📍 `{esc(address[:6])}…{esc(address[-4:])}`  \\({esc(chain.capitalize())}\\)",
        f"{direction} Score: *{esc(str(int(old_score)))}* ──▶ *{esc(str(int(new_score)))}* \\({esc(delta_str)}\\)",
        f"   Grade: {esc(old_grade)} ──▶ {esc(new_grade)}",
    ]

    if override_status == "ofac_active":
        lines.append("⛔ *OFAC SANCTION APPLIED*")
    elif override_status == "exploit_active":
        lines.append("💀 *EXPLOIT FLAG APPLIED*")

    if new_flags:
        lines.append("")
        lines.append("🚨 *New Flags:*")
        for flag in new_flags[:5]:  # cap at 5
            lines.append(f"   • {esc(flag)}")

    if sub_scores:
        lines += [
            "",
            "📊 *Sub\\-scores:*",
            f"   Code Risk    `{progress_bar(sub_scores.get('code', 0))}`",
            f"   Ownership    `{progress_bar(sub_scores.get('ownership', 0))}`",
            f"   Liquidity    `{progress_bar(sub_scores.get('liquidity', 0))}`",
            f"   Audit        `{progress_bar(sub_scores.get('audit', 0))}`",
            f"   Compliance   `{progress_bar(sub_scores.get('compliance', 0))}`",
            f"   Governance   `{progress_bar(sub_scores.get('governance', 0))}`",
        ]

    lines += [
        "",
        f"🔗 [View full report](https://privascan\\.xyz/score/{esc(chain)}/{esc(address)})",
        "━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)


# ── Help message ───────────────────────────────────────────────────────────────
def format_help() -> str:
    return "\n".join([
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "🛡 *PRIVASCAN BOT*",
        "_EVM Privacy Protocol Smart Contract Risk Scanner_",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        "*Commands:*",
        "",
        "🔍 `/scan <chain> <address>`",
        "   Score any EVM contract",
        "   _Example: /scan ethereum 0x910C…_",
        "",
        "📋 `/protocols`",
        "   List all 14 curated privacy protocols",
        "",
        "👁 `/watch <chain> <address> [threshold]`",
        "   Get alerts when score changes",
        "   _Threshold default: 10 points_",
        "   _Example: /watch ethereum 0x910C… 15_",
        "",
        "🚫 `/unwatch <chain> <address>`",
        "   Stop watching a contract",
        "",
        "📌 `/watchlist`",
        "   Show all contracts you're watching",
        "",
        "❓ `/help`",
        "   Show this message",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "Chains: `ethereum` · `polygon` · `arbitrum`",
        "`optimism` · `base` · `bnb` · `avalanche`",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "🌐 [privascan\\.xyz](https://privascan.xyz)",
    ])


# ── Watchlist display ──────────────────────────────────────────────────────────
def format_watchlist(items: list[dict]) -> str:
    if not items:
        return "\n".join([
            "📌 *Your Watchlist*",
            "",
            "_Nothing here yet\\._",
            "Use `/watch <chain> <address>` to start monitoring a contract\\.",
        ])

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "📌 *YOUR WATCHLIST*",
        f"_{esc(str(len(items)))} contract{'s' if len(items) != 1 else ''} monitored_",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for item in items:
        addr    = item.get("address", "")
        chain   = item.get("chain_name", "")
        thresh  = item.get("threshold_score")
        score   = item.get("last_score")
        grade   = item.get("last_grade", "?")
        proto   = item.get("protocol_name", "")

        short = f"{addr[:6]}…{addr[-4:]}" if len(addr) > 10 else addr
        score_str = f"{grade_emoji(grade)} {int(score)}/100" if score is not None else "Not scored"
        thresh_str = f"Alert at ±{int(thresh)}pts" if thresh else "Alert at ±10pts"
        proto_str = f" · {esc(proto)}" if proto else ""

        lines += [
            f"• `{esc(short)}` \\({esc(chain.capitalize())}{proto_str}\\)",
            f"  {esc(score_str)} · {esc(thresh_str)}",
            f"  `/unwatch {esc(chain)} {esc(addr)}`",
            "",
        ]

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
