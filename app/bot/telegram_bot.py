"""
Day 10 — Telegram bot — all commands implemented.
"""

from __future__ import annotations

import asyncio
import logging
import re

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest
from telegram.constants import ParseMode

from app.config import settings
from app.bot.formatters import (
    format_scan_result,
    format_protocol_list,
    format_alert,
    format_help,
    format_watchlist,
    esc,
)
from app.bot.alerts import AlertSubscriber

log = logging.getLogger(__name__)

API_BASE = "http://api:8000/api/v1"

VALID_CHAINS = {
    "ethereum", "polygon", "arbitrum",
    "optimism", "base", "bnb", "avalanche",
}

ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DEFAULT_THRESHOLD = 10.0


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def _api_get(path: str, timeout: float = 130.0) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(f"{API_BASE}{path}")
            r.raise_for_status()
            return r.json()
    except httpx.TimeoutException:
        log.warning("api.timeout path=%s", path)
        return None
    except Exception as exc:
        log.error("api.error path=%s: %s", path, exc)
        return None


def _parse_chain_address(args: tuple) -> tuple[str | None, str | None, str | None]:
    if len(args) < 2:
        return None, None, (
            "Usage: `/scan <chain> <address>`\n"
            "Example: `/scan ethereum 0x910Cbd523D972eb0a6f4cae4618aD62622b39DbF`"
        )
    chain = args[0].lower()
    address = args[1].lower()

    if chain not in VALID_CHAINS:
        chains = " · ".join(f"`{c}`" for c in sorted(VALID_CHAINS))
        return None, None, f"Unknown chain `{esc(chain)}`\\.\nSupported: {chains}"

    if not ADDRESS_RE.match(address):
        return None, None, (
            f"Invalid address `{esc(address)}`\\.\n"
            "Must be `0x` \\+ 40 hex characters\\."
        )

    return chain, address, None


async def _get_watchlist_items(chat_id: int) -> list[dict]:
    try:
        from app.db.session import AsyncSessionLocal
        from app.db.models import Watchlist, Contract, ScoreReport, Protocol
        from sqlalchemy import select

        items = []
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Watchlist, Contract)
                .join(Contract, Watchlist.contract_id == Contract.id)
                .where(Watchlist.telegram_chat_id == chat_id)
                .order_by(Watchlist.created_at.desc())
            )
            rows = result.all()

            for wl, contract in rows:
                sr = await db.execute(
                    select(ScoreReport)
                    .where(ScoreReport.contract_id == contract.id)
                    .order_by(ScoreReport.scored_at.desc())
                    .limit(1)
                )
                latest = sr.scalar_one_or_none()

                proto_name = None
                if contract.protocol_id:
                    pr = await db.execute(
                        select(Protocol).where(Protocol.id == contract.protocol_id)
                    )
                    proto = pr.scalar_one_or_none()
                    if proto:
                        proto_name = proto.name

                items.append({
                    "address": contract.address,
                    "chain_name": contract.chain_name or "ethereum",
                    "threshold_score": float(wl.threshold_score) if wl.threshold_score else DEFAULT_THRESHOLD,
                    "last_score": float(latest.composite_score) if latest else None,
                    "last_grade": latest.grade if latest else None,
                    "protocol_name": proto_name,
                })

        return items
    except Exception as exc:
        log.error("watchlist.fetch_error chat_id=%s: %s", chat_id, exc)
        return []


async def _upsert_watchlist(chat_id: int, address: str, chain: str, threshold: float) -> str:
    try:
        from app.db.session import AsyncSessionLocal
        from app.db.models import Watchlist, Contract
        from app.core.clients.chains import CHAINS
        from sqlalchemy import select

        chain_id = CHAINS[chain].chain_id

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Contract).where(
                    Contract.address == address,
                    Contract.chain_id == chain_id,
                )
            )
            contract = result.scalar_one_or_none()

            if not contract:
                contract = Contract(
                    address=address,
                    chain_id=chain_id,
                    chain_name=chain,
                    scan_type="community",
                )
                db.add(contract)
                await db.flush()

            wl_result = await db.execute(
                select(Watchlist).where(
                    Watchlist.telegram_chat_id == chat_id,
                    Watchlist.contract_id == contract.id,
                )
            )
            existing = wl_result.scalar_one_or_none()

            if existing:
                existing.threshold_score = threshold
                status = "updated"
            else:
                db.add(Watchlist(
                    telegram_chat_id=chat_id,
                    contract_id=contract.id,
                    threshold_score=threshold,
                ))
                status = "added"

            await db.commit()
            return status
    except Exception as exc:
        log.error("watchlist.upsert_error: %s", exc)
        return "error"


async def _remove_watchlist(chat_id: int, address: str, chain: str) -> bool:
    try:
        from app.db.session import AsyncSessionLocal
        from app.db.models import Watchlist, Contract
        from app.core.clients.chains import CHAINS
        from sqlalchemy import select, delete

        chain_id = CHAINS[chain].chain_id

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Contract).where(
                    Contract.address == address,
                    Contract.chain_id == chain_id,
                )
            )
            contract = result.scalar_one_or_none()
            if not contract:
                return False

            result = await db.execute(
                delete(Watchlist).where(
                    Watchlist.telegram_chat_id == chat_id,
                    Watchlist.contract_id == contract.id,
                ).returning(Watchlist.id)
            )
            deleted = result.fetchone()
            await db.commit()
            return deleted is not None
    except Exception as exc:
        log.error("watchlist.remove_error: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        format_help(),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        format_help(),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chain, address, err = _parse_chain_address(tuple(context.args or []))
    if err:
        await update.message.reply_text(err, parse_mode=ParseMode.MARKDOWN_V2)
        return

    msg = await update.message.reply_text(
        f"⏳ *Scanning* `{esc(address[:6])}…{esc(address[-4:])}` on "
        f"{esc(chain.capitalize())}\\.\\.\\.\n\n"
        "_This may take 30–60 seconds\\._",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    result = await _api_get(f"/score/{chain}/{address}")

    if result is None:
        await msg.edit_text(
            f"❌ Scoring failed or timed out for `{esc(address)}`\\.\n"
            "Please try again or use privascan\\.xyz",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    await msg.edit_text(
        format_scan_result(result),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def cmd_protocols(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text(
        "⏳ _Fetching protocol directory\\.\\.\\._",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    result = await _api_get("/protocols/")
    if result is None:
        await msg.edit_text(
            "❌ Could not fetch protocols\\. Please try again\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    protocols = result.get("protocols", [])
    enriched = []
    for p in protocols:
        detail = await _api_get(f"/protocols/{p['slug']}")
        if detail:
            p["latest_score"] = detail.get("latest_score")
        enriched.append(p)

    await msg.edit_text(
        format_protocol_list(enriched),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


async def cmd_watch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args or []
    chain, address, err = _parse_chain_address(tuple(args))
    if err:
        await update.message.reply_text(
            err + "\n\nExample: `/watch ethereum 0x910C… 15`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    threshold = DEFAULT_THRESHOLD
    if len(args) >= 3:
        try:
            threshold = max(1.0, min(50.0, float(args[2])))
        except ValueError:
            pass

    chat_id = update.effective_chat.id
    status = await _upsert_watchlist(chat_id, address, chain, threshold)

    if status == "error":
        await update.message.reply_text(
            "❌ Failed to add to watchlist\\. Please try again\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    verb = "Updated" if status == "updated" else "Added"
    await update.message.reply_text(
        f"✅ *{verb}\\!*\n\n"
        f"📍 `{esc(address)}`\n"
        f"🔗 Chain: {esc(chain.capitalize())}\n"
        f"🔔 Alert when score changes ≥ {esc(str(int(threshold)))} points\n\n"
        f"Use `/unwatch {esc(chain)} {esc(address)}` to stop monitoring\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def cmd_unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chain, address, err = _parse_chain_address(tuple(context.args or []))
    if err:
        await update.message.reply_text(err, parse_mode=ParseMode.MARKDOWN_V2)
        return

    chat_id = update.effective_chat.id
    removed = await _remove_watchlist(chat_id, address, chain)

    if removed:
        await update.message.reply_text(
            f"✅ Removed `{esc(address[:6])}…{esc(address[-4:])}` "
            f"\\({esc(chain.capitalize())}\\) from your watchlist\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    else:
        await update.message.reply_text(
            f"⚠️ `{esc(address[:6])}…{esc(address[-4:])}` wasn't in your watchlist\\.",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def cmd_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    items = await _get_watchlist_items(chat_id)
    await update.message.reply_text(
        format_watchlist(items),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ALERT DISPATCHER
# ─────────────────────────────────────────────────────────────────────────────

async def _dispatch_alert(bot, payload: dict) -> None:
    chat_id = payload.get("chat_id")
    if not chat_id:
        return
    try:
        text = format_alert(
            address=payload.get("address", ""),
            chain=payload.get("chain", ""),
            old_score=float(payload.get("old_score", 0)),
            new_score=float(payload.get("new_score", 0)),
            old_grade=payload.get("old_grade", "?"),
            new_grade=payload.get("new_grade", "?"),
            sub_scores=payload.get("sub_scores", {}),
            new_flags=payload.get("new_flags"),
            protocol_name=payload.get("protocol_name"),
            override_status=payload.get("override_status"),
        )
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
        log.info("alert.sent chat_id=%s", chat_id)
    except Exception as exc:
        log.error("alert.send_failed chat_id=%s: %s", chat_id, exc)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT — with retry loop
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    log.info("bot.start token_set=%s", bool(settings.telegram_bot_token))

    if not settings.telegram_bot_token:
        log.error("bot.no_token — set TELEGRAM_BOT_TOKEN in .env")
        return

    # Retry loop — handles transient Telegram API timeouts on startup
    retry_delay = 5
    max_retries = 12  # ~1 minute total

    for attempt in range(1, max_retries + 1):
        try:
            log.info("bot.connect_attempt=%d", attempt)

            # Generous timeouts for flaky connections
            request = HTTPXRequest(
                connection_pool_size=8,
                connect_timeout=30.0,
                read_timeout=30.0,
                write_timeout=30.0,
                pool_timeout=30.0,
            )

            app = (
                Application.builder()
                .token(settings.telegram_bot_token)
                .request(request)
                .build()
            )

            app.add_handler(CommandHandler("start",     cmd_start))
            app.add_handler(CommandHandler("help",      cmd_help))
            app.add_handler(CommandHandler("scan",      cmd_scan))
            app.add_handler(CommandHandler("protocols", cmd_protocols))
            app.add_handler(CommandHandler("watch",     cmd_watch))
            app.add_handler(CommandHandler("unwatch",   cmd_unwatch))
            app.add_handler(CommandHandler("watchlist", cmd_watchlist))

            subscriber = AlertSubscriber(
                lambda payload: _dispatch_alert(app.bot, payload)
            )

            async with app:
                await app.start()
                await app.updater.start_polling(
                    drop_pending_updates=True,
                    timeout=20,
                )
                log.info("bot.polling_started attempt=%d", attempt)

                try:
                    await subscriber.run()
                finally:
                    subscriber.stop()
                    await app.updater.stop()
                    await app.stop()

            break  # clean exit — don't retry

        except Exception as exc:
            log.warning("bot.connect_failed attempt=%d/%d: %s",
                        attempt, max_retries, exc)
            if attempt < max_retries:
                log.info("bot.retry_in=%ds", retry_delay)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)  # exponential backoff, cap 60s
            else:
                log.error("bot.failed_all_attempts — giving up")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(main())
