#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pocket X — Single Bot Backend (fixed)
Markets 4x goX | OTP | Live trades | Deposit verify | Bonus | Admin + Start Message
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

import requests
import firebase_admin
from firebase_admin import credentials, db, auth as fb_auth

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

# ===================== CONFIG =====================
BOT_TOKEN = os.environ.get(
    "BOT_TOKEN", "8672213562:AAFOLTcKbagfW7TnlQALzEN0v2de6aTuJuY"
)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "https://pocket-x-70da1-default-rtdb.firebaseio.com"
)
FIREBASE_CRED_PATH = os.environ.get("FIREBASE_CRED_PATH", "").strip()
RUPANTOR_API_KEY = os.environ.get(
    "RUPANTOR_API_KEY", "QkfXAWXtJXMQXG1VMO8SAUOSLECKbKTOz2MYm0vHsuVifeB6R0"
)
ADMIN_IDS = {
    int(x)
    for x in os.environ.get("ADMIN_IDS", "7500420695").split(",")
    if x.strip().isdigit()
}

PAYOUT_MULT = 1.96
MAX_TRADES_PER_CANDLE = 10
MIN_TRADE = 2.0
MAX_TRADE = 2000.0
OTP_TTL_MS = 120_000
TRADE_BLOCK_LAST_SECONDS = 2

FIREBASE_JSON_NAMES = (
    "pocket-x-adminfirebase-config.json",
    "firebase-config.json",
    "serviceAccount.json",
    "serviceAccountKey.json",
    "service-account.json",
)

# Embedded service account — 2-file free host fallback
FIREBASE_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "pocket-x-70da1",
    "private_key_id": "014d028311fda242d546c75caa1ff1d663090afb",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCwUF8VUfnsUNSb\nxHhNBlG6kJcI1cJSb6CkvkNgsMANEy4Rr+5HU2RVlo5Tw5VUHmt19Ms1w3ZJnJyE\nu3uwLy92M2jYfJlOjN8iIS0o5I81u2zbMS0+G5nZ6fwNXnxULJGHpc2qoxE2rE19\nmiLu6jG5hAPrt/3TfeI7gpqUsDQC7ASuc+DH1ZFhjsAhy7YEencLpnMrqm7axHIv\nWVDNSWphSqa0NOy5YXJyUlp2kiCz5TtjnuspPLE9KjEGfpNolne9ScP6B+4LejF1\nDPT8G+/niCdqJTwx6O1v6WNAbH7ruEgv5tVTWEqZKTs01cyrFcFDY0/XGH04l/+Z\nR/p/FGwrAgMBAAECggEAFRfgcDwI8tkuvl3waIKfh3rh3tg38cXSCbOLewdaSpYn\nVk1ea+ERqV2kNGg7Nr+W6ps5LnrubVsTrJuDbi4O9wyqd+/cJXYcAcjHTtOdQHfm\nS4jkGUCTFOt10KGjrSxR0tEmvEna9tgBQ0wL7tpMzZ16HJq7/q/aP3VeCfjUmB6y\nkNcLYfYAMr/+ueBtQr0pC3RQsEC8B07jsxDU8UQDbSukUCd+GEhJe9dvWo7FC2sy\nhtNX2quMgAsoddC+6viRJBpB05+OugVmA+A576gOy9L43zbQZmcqkl8ki9372GU+\naNtgRURu7nPwXH2kycJS34VaNvnXN6rWlGWJkcnGrQKBgQDVxy64H6vapkNDUj76\nXQutEIJvISBpB/c+NRtf+YFA2a5SV6jD09b/jRMOnwOIPqDsPC7CE6BI9jhCVo3l\n8f6iahGAGd3CEcNJA5F+qYR/G86McMPs+k9BDxFQmwU+50yOXZ9I4hH8f5oqoGBA\nGUZ1b5QzYo16kuq8R9jb5YaHVQKBgQDTIvgHqbOLcc66m15U3QP+pK960r27kt+m\njR8Rp5cZDSJ11d5Zt5rQiMhG7aQw2bF+8CGxvqHF2hCwgRymnaToB09A9RCtH7Mm\n5UmT4CZruPEjZnHTvYx7scdf4bVtB9R10ow1nmydUJinZadht+S6LSraSywi+Kx8\n0zv04KglfwKBgFpOkzDayDlMhRuaUdpnlfgdAky5vLxBzjMsMg1AFFb13gsQ1s0q\n3ycDTGqfx9k1Q7unzMTVj59iy+9SKw1ZRg0MK6pmwuQppspgRIUyTTN45q8zL8Eb\nGIHOQK1BX1zsTs3RROl//sMgkFqzdxV81+PiJ8PxPPzrtVemLjjuY/8lAoGBAKVZ\nxH9T0s3JMkqINQcnE+LQHLGG65pDuy2XZZaQ9k9jLvKzrG/8z5yzEo4hvC2Zv10X\nOHwYPF9TmTBx3PtLiINCfjnz8rxyj/5NISNTLyO78fV0XH6j+qpAn1Ci1k/uCuC/\nJJk1WgCVxweKH9zyhImdp+rPZmB4+bTERTdQ3b6HAoGAPkcAeMqMbsQW5cQv2JRX\nb22S3EDOw0Phs87mawNQRSiT2ilB7Pla13wHoY/TkjbBf/bHUsd6MMlyaKc+KMjq\nqCaCH3KW7RATpxv1cKWz0Uvmj4bdnFx0XH07tM4ND2Jj7CZwoJzW0A4rg7RorNiY\n1ecqJzL1gQMFMeKbzrbiHpE=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@pocket-x-70da1.iam.gserviceaccount.com",
    "client_id": "100911321963325396073",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40pocket-x-70da1.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}

def number_direction(n: int) -> str:
    return "HIGH" if int(n) >= 5 else "LOW"


CANDLE_NAMES = {
    0: "Silent Drop",
    1: "Trapped",
    2: "Chaos",
    3: "Shadow Low",
    4: "Deep Red",
    5: "Rebel Rise",
    6: "Sky Break",
    7: "Phoenix",
    8: "Green Pulse",
    9: "Peak High",
}

MARKETS = {
    "gox30s": {
        "node": "GoX30s_Market",
        "interval": 30,
        "api": "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json",
    },
    "gox1m": {
        "node": "GoX1m_Market",
        "interval": 60,
        "api": "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json",
    },
    "gox3m": {
        "node": "GoX3m_Market",
        "interval": 180,
        "api": "https://draw.ar-lottery01.com/WinGo/WinGo_3M/GetHistoryIssuePage.json",
    },
    "gox5m": {
        "node": "GoX5m_Market",
        "interval": 300,
        "api": "https://draw.ar-lottery01.com/WinGo/WinGo_5M/GetHistoryIssuePage.json",
    },
}

# Admin conversation states
(
    NOTIFY_CHOOSE,
    NOTIFY_USER_ID,
    NOTIFY_MESSAGE,
    START_MSG_WAIT,
) = range(4)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("pocketx-bot")

_last_period: Dict[str, str] = {}
_last_number: Dict[str, int] = {}
_settled_periods: Set[str] = set()
_processed_otp: Set[str] = set()
_processed_trades: Set[str] = set()
_processed_bonus: Set[str] = set()
_processed_deposits: Set[str] = set()


# ===================== FIREBASE =====================
def _is_service_account_json(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return bool(
            isinstance(data, dict)
            and data.get("private_key")
            and (data.get("type") == "service_account" or data.get("client_email"))
        )
    except Exception:
        return False


def find_firebase_cred_file() -> Optional[str]:
    candidates = []
    if FIREBASE_CRED_PATH:
        candidates.append(FIREBASE_CRED_PATH)
    bases = []
    try:
        bases.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    bases.extend([os.getcwd(), "/app", "/workspace", "/data"])
    for base in bases:
        if not base or not os.path.isdir(base):
            continue
        for name in FIREBASE_JSON_NAMES:
            candidates.append(os.path.join(base, name))
    seen = set()
    for path in candidates:
        ap = os.path.abspath(path)
        if ap in seen:
            continue
        seen.add(ap)
        if os.path.isfile(ap) and _is_service_account_json(ap):
            return ap
    return None


def init_firebase() -> None:
    if firebase_admin._apps:
        return
    path = find_firebase_cred_file()
    if path:
        cred = credentials.Certificate(path)
        src = path
    else:
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
        src = "embedded"
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
    log.info("Firebase Admin initialized (%s)", src)


def uref(tid: str):
    return db.reference(f"users/{tid}")


def list_user_telegram_ids() -> list:
    """Collect telegram ids from users node; tolerate structure."""
    ids = []
    try:
        users = db.reference("users").get() or {}
    except Exception as e:
        log.exception("list users failed: %s", e)
        raise
    if not isinstance(users, dict):
        return ids
    for k, v in users.items():
        if str(k).isdigit():
            ids.append(int(k))
        elif isinstance(v, dict):
            tid = v.get("telegram_id") or v.get("id")
            if tid and str(tid).isdigit():
                ids.append(int(tid))
    # unique
    return sorted(set(ids))


# ===================== WINGO / MARKETS =====================
def fetch_wingo(api_url: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(api_url, params={"t": int(time.time() * 1000)}, timeout=12)
        r.raise_for_status()
        data = r.json()
        lst = (data.get("data") or {}).get("list") or []
        if not lst:
            return None
        item = lst[0]
        issue = str(item.get("issueNumber") or item.get("issue") or "")
        num_raw = item.get("number")
        if num_raw is None or not issue:
            return None
        number = int(str(num_raw).strip())
        if number < 0 or number > 9:
            return None
        return {
            "issueNumber": issue,
            "periodShort": issue[-4:] if len(issue) >= 4 else issue,
            "number": number,
            "direction": number_direction(number),
            "candleName": CANDLE_NAMES.get(number, str(number)),
        }
    except Exception as e:
        log.warning("WinGo fetch error: %s", e)
        return None


def write_market_node(market_id: str, payload: Dict[str, Any]) -> None:
    m = MARKETS[market_id]
    body = {
        "number": payload["number"],
        "period": payload["issueNumber"],
        "periodShort": payload["periodShort"],
        "direction": payload["direction"],
        "candleName": payload.get("candleName") or CANDLE_NAMES.get(payload["number"], ""),
        "updatedAt": int(time.time() * 1000),
    }
    # overwrite node only — do NOT push unbounded list
    db.reference(m["node"]).update(body)
    _last_period[market_id] = payload["issueNumber"]
    _last_number[market_id] = int(payload["number"])


def seconds_into_window(interval: int) -> int:
    return int(time.time()) % interval


def seconds_left_in_window(interval: int) -> int:
    return interval - seconds_into_window(interval)


async def market_loop(app: Application) -> None:
    while True:
        try:
            for mid, cfg in MARKETS.items():
                interval = cfg["interval"]
                left = seconds_left_in_window(interval)

                # refresh when period changes or near end
                if left <= 3 or left % 5 == 0:
                    data = fetch_wingo(cfg["api"])
                    if not data:
                        continue
                    prev = _last_period.get(mid)
                    if data["issueNumber"] != prev:
                        # settle previous period before switching
                        if prev and f"{mid}:{prev}" not in _settled_periods:
                            await settle_market_period(mid, prev)
                            _settled_periods.add(f"{mid}:{prev}")
                        write_market_node(mid, data)
                        log.info(
                            "Market %s period=%s number=%s",
                            mid,
                            data["issueNumber"],
                            data["number"],
                        )
                    elif left <= 3:
                        # keep node fresh near close
                        write_market_node(mid, data)

                # right after rollover settle
                if left >= interval - 1:
                    period = _last_period.get(mid)
                    if period and f"{mid}:{period}" not in _settled_periods:
                        await settle_market_period(mid, period)
                        _settled_periods.add(f"{mid}:{period}")
                        if len(_settled_periods) > 400:
                            _settled_periods.clear()
        except Exception as e:
            log.exception("market_loop: %s", e)
        await asyncio.sleep(1)


# ===================== TRADES =====================
async def settle_market_period(market_id: str, period: str) -> None:
    if not period:
        return
    number = _last_number.get(market_id)
    if number is None:
        snap = db.reference(MARKETS[market_id]["node"]).get() or {}
        if str(snap.get("period") or "") == period and snap.get("number") is not None:
            number = int(snap["number"])
        else:
            data = fetch_wingo(MARKETS[market_id]["api"])
            if not data:
                log.warning("No number settle %s %s", market_id, period)
                return
            # only use if API period matches
            if data["issueNumber"] != period:
                log.warning(
                    "Period mismatch settle mid=%s want=%s api=%s",
                    market_id,
                    period,
                    data["issueNumber"],
                )
                return
            number = int(data["number"])

    direction = number_direction(int(number))
    try:
        logs = (
            db.reference("Trade_Logs")
            .order_by_child("status")
            .equal_to("pending")
            .get()
        )
    except Exception as e:
        log.warning("Trade_Logs query: %s", e)
        logs = db.reference("Trade_Logs").get() or {}

    if not isinstance(logs, dict):
        return

    node_name = MARKETS[market_id]["node"]
    for key, trade in logs.items():
        if not isinstance(trade, dict):
            continue
        if trade.get("status") != "pending":
            continue
        if not trade.get("bot_accepted"):
            continue
        mid = str(trade.get("market") or "")
        if mid not in (market_id, node_name):
            continue
        t_period = str(trade.get("period") or trade.get("issueNumber") or "")
        # MUST match period — no period-less settle
        if not t_period or t_period != period:
            continue
        await settle_one_trade(key, trade, int(number), direction)


async def settle_one_trade(
    key: str, trade: Dict[str, Any], number: int, candle_dir: str
) -> None:
    if key in _processed_trades:
        return
    if trade.get("status") != "pending":
        return
    tid = str(trade.get("telegram_id") or "")
    if not tid:
        return
    amount = float(trade.get("amount") or 0)
    user_dir = str(trade.get("direction") or "").upper()
    if user_dir in ("UP", "CALL", "BUY"):
        user_dir = "HIGH"
    if user_dir in ("DOWN", "PUT", "SELL"):
        user_dir = "LOW"
    won = user_dir == candle_dir
    payout = round(amount * PAYOUT_MULT, 2) if won else 0.0

    try:
        if won:

            def _bal_tx(current):
                return round(float(current or 0) + payout, 2)

            uref(tid).child("balance").transaction(_bal_tx)

        db.reference(f"Trade_Logs/{key}").update(
            {
                "status": "won" if won else "lost",
                "payout": payout,
                "resultNumber": number,
                "resultDirection": candle_dir,
                "candleName": CANDLE_NAMES.get(number, ""),
                "resolvedAt": int(time.time() * 1000),
            }
        )
        if won and payout:
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            pref = db.reference(f"Today_Profit/{day}")
            try:
                pref.child("total_payouts").transaction(
                    lambda c: round(float(c or 0) + payout, 2)
                )
                pref.child("wins").transaction(lambda c: int(c or 0) + 1)
            except Exception:
                pass
        _processed_trades.add(key)
        log.info(
            "Settled %s tid=%s %s payout=%s n=%s",
            key,
            tid,
            "WON" if won else "LOST",
            payout,
            number,
        )
    except Exception as e:
        log.exception("settle_one_trade %s: %s", key, e)


async def trade_intake_loop(app: Application) -> None:
    while True:
        try:
            try:
                logs = (
                    db.reference("Trade_Logs")
                    .order_by_child("status")
                    .equal_to("pending")
                    .get()
                )
            except Exception:
                logs = db.reference("Trade_Logs").get() or {}
            if isinstance(logs, dict):
                for key, trade in logs.items():
                    if not isinstance(trade, dict):
                        continue
                    if trade.get("bot_accepted") or trade.get("status") != "pending":
                        continue
                    mode = str(trade.get("mode") or "live").lower()
                    if mode in ("demo", "ai"):
                        continue
                    await accept_trade(key, trade)
        except Exception as e:
            log.exception("trade_intake_loop: %s", e)
        await asyncio.sleep(1)


def resolve_market_id(market: str) -> Optional[str]:
    if market in MARKETS:
        return market
    for k, v in MARKETS.items():
        if market == v["node"]:
            return k
    # frontend sometimes uses goX30s style
    aliases = {
        "gox30": "gox30s",
        "goX30s": "gox30s",
        "goX1m": "gox1m",
        "goX3m": "gox3m",
        "goX5m": "gox5m",
    }
    return aliases.get(market)


async def accept_trade(key: str, trade: Dict[str, Any]) -> None:
    tid = str(trade.get("telegram_id") or "")
    amount = float(trade.get("amount") or 0)
    market = str(trade.get("market") or "")
    if not tid or amount < MIN_TRADE or amount > MAX_TRADE:
        db.reference(f"Trade_Logs/{key}").update(
            {"status": "rejected", "reason": "invalid", "bot_accepted": True}
        )
        return

    mid = resolve_market_id(market)
    if not mid:
        db.reference(f"Trade_Logs/{key}").update(
            {"status": "rejected", "reason": "bad_market", "bot_accepted": True}
        )
        return

    interval = MARKETS[mid]["interval"]
    left = seconds_left_in_window(interval)
    if left <= TRADE_BLOCK_LAST_SECONDS:
        db.reference(f"Trade_Logs/{key}").update(
            {
                "status": "rejected",
                "reason": "candle_closing",
                "bot_accepted": True,
            }
        )
        return

    period = str(trade.get("period") or trade.get("issueNumber") or "").strip()
    if not period:
        period = _last_period.get(mid) or ""
    if not period:
        # try from node
        snap = db.reference(MARKETS[mid]["node"]).get() or {}
        period = str(snap.get("period") or "")
    if not period:
        db.reference(f"Trade_Logs/{key}").update(
            {"status": "rejected", "reason": "no_period", "bot_accepted": True}
        )
        return

    # max 10 per period
    count = 0
    try:
        all_logs = (
            db.reference("Trade_Logs")
            .order_by_child("telegram_id")
            .equal_to(tid)
            .get()
            or {}
        )
    except Exception:
        all_logs = {}
    if isinstance(all_logs, dict):
        for t in all_logs.values():
            if not isinstance(t, dict):
                continue
            if str(t.get("period") or "") != period:
                continue
            if str(t.get("market") or "") not in (market, mid, MARKETS[mid]["node"]):
                continue
            if t.get("bot_accepted") and t.get("status") in (
                "pending",
                "won",
                "lost",
            ):
                count += 1
    if count >= MAX_TRADES_PER_CANDLE:
        db.reference(f"Trade_Logs/{key}").update(
            {
                "status": "rejected",
                "reason": "max_trades",
                "bot_accepted": True,
            }
        )
        return

    deducted = {"ok": False}

    def _deduct(current):
        cur = float(current or 0)
        if cur < amount:
            return cur
        deducted["ok"] = True
        return round(cur - amount, 2)

    try:
        uref(tid).child("balance").transaction(_deduct)
        if not deducted["ok"]:
            db.reference(f"Trade_Logs/{key}").update(
                {
                    "status": "rejected",
                    "reason": "insufficient",
                    "bot_accepted": True,
                }
            )
            return
        db.reference(f"Trade_Logs/{key}").update(
            {
                "bot_accepted": True,
                "period": period,
                "market": mid,
                "acceptedAt": int(time.time() * 1000),
            }
        )
        log.info("Accepted trade %s tid=%s amount=%s period=%s", key, tid, amount, period)
    except Exception as e:
        log.exception("accept_trade: %s", e)


# ===================== OTP =====================
async def otp_loop(app: Application) -> None:
    while True:
        try:
            reqs = db.reference("OTP_Requests").get() or {}
            if isinstance(reqs, dict):
                for key, row in list(reqs.items()):
                    if not isinstance(row, dict):
                        continue
                    if row.get("sent") or key in _processed_otp:
                        continue
                    await process_otp_request(app, key, row)
            ver = db.reference("OTP_Verify").get() or {}
            if isinstance(ver, dict):
                for key, row in list(ver.items()):
                    if not isinstance(row, dict) or row.get("done"):
                        continue
                    await process_otp_verify(app, key, row)
        except Exception as e:
            log.exception("otp_loop: %s", e)
        await asyncio.sleep(1)


async def process_otp_request(app: Application, key: str, row: Dict[str, Any]) -> None:
    tid = str(row.get("telegram_id") or "")
    if not tid:
        return
    code = str(row.get("code") or "").strip()
    if not code:
        code = str(random.randint(100000, 999999))
        db.reference(f"OTP_Requests/{key}").update({"code": code})
    purpose = str(row.get("purpose") or "verification")
    created = int(row.get("createdAt") or time.time() * 1000)
    if int(time.time() * 1000) - created > OTP_TTL_MS * 2:
        db.reference(f"OTP_Requests/{key}").update(
            {"sent": True, "expired": True, "bot_skip": True}
        )
        _processed_otp.add(key)
        return
    msg = (
        f"🔐 <b>Pocket X OTP</b>\n"
        f"Purpose: {purpose}\n"
        f"Code: <code>{code}</code>\n"
        f"Valid ~2 minutes. Do not share."
    )
    try:
        await app.bot.send_message(chat_id=int(tid), text=msg, parse_mode="HTML")
        db.reference(f"OTP_Requests/{key}").update(
            {
                "sent": True,
                "sentAt": int(time.time() * 1000),
                "code": code,
                "expiresAt": int(time.time() * 1000) + OTP_TTL_MS,
            }
        )
        _processed_otp.add(key)
        log.info("OTP sent to %s purpose=%s", tid, purpose)
    except Exception as e:
        log.warning("OTP send fail %s: %s", tid, e)
        db.reference(f"OTP_Requests/{key}").update(
            {"send_error": str(e)[:200], "sent": False}
        )


async def process_otp_verify(app: Application, key: str, row: Dict[str, Any]) -> None:
    tid = str(row.get("telegram_id") or "")
    submitted = str(row.get("code") or "").strip()
    purpose = str(row.get("purpose") or "verification")
    if not tid or not submitted:
        return
    reqs = db.reference("OTP_Requests").get() or {}
    matched = False
    match_key = None
    now = int(time.time() * 1000)
    if isinstance(reqs, dict):
        for rk, rv in reqs.items():
            if not isinstance(rv, dict):
                continue
            if str(rv.get("telegram_id")) != tid:
                continue
            if str(rv.get("purpose") or "verification") != purpose:
                continue
            if not rv.get("sent"):
                continue
            exp = int(rv.get("expiresAt") or 0)
            if exp and now > exp:
                continue
            created = int(rv.get("createdAt") or 0)
            if created and now - created > OTP_TTL_MS:
                continue
            if str(rv.get("code") or "") == submitted:
                matched = True
                match_key = rk
                break
    if matched:
        db.reference(f"OTP_Verify/{key}").update(
            {"done": True, "ok": True, "verifiedAt": now}
        )
        if match_key:
            try:
                db.reference(f"OTP_Requests/{match_key}").delete()
            except Exception:
                pass
        if purpose == "verification" and row.get("profile"):
            await apply_verification(tid, row.get("profile") or {})
        log.info("OTP verified tid=%s", tid)
    else:
        db.reference(f"OTP_Verify/{key}").update(
            {"done": True, "ok": False, "reason": "mismatch_or_expired"}
        )


async def apply_verification(tid: str, profile: Dict[str, Any]) -> None:
    updates = {
        "fullName": profile.get("fullName") or profile.get("name"),
        "mobileNumber": profile.get("mobileNumber") or profile.get("mobile"),
        "email": profile.get("email"),
        "isVerified": True,
        "verified": True,
        "liveness_verified": True,
        "face_lock": True,
        "face_verified_at": int(time.time() * 1000),
        "verified_by": "bot",
    }
    updates = {k: v for k, v in updates.items() if v is not None}
    uref(tid).update(updates)
    email = profile.get("email")
    password = profile.get("password")
    if email and password:
        try:
            try:
                fb_auth.create_user(email=email, password=password, uid=f"tg_{tid}")
            except Exception:
                try:
                    fb_auth.update_user(f"tg_{tid}", email=email, password=password)
                except Exception as e2:
                    log.warning("auth update %s: %s", tid, e2)
            uref(tid).update({"firebase_uid": f"tg_{tid}"})
        except Exception as e:
            log.warning("create_user %s: %s", tid, e)


# ===================== DEPOSIT =====================
def rupantor_verify(transaction_id: str) -> Optional[Dict[str, Any]]:
    try:
        r = requests.post(
            "https://payment.rupantorpay.com/api/payment/verify-payment",
            headers={
                "X-API-KEY": RUPANTOR_API_KEY,
                "Content-Type": "application/json",
            },
            json={"transaction_id": transaction_id},
            timeout=20,
        )
        return r.json()
    except Exception as e:
        log.warning("rupantor_verify: %s", e)
        return None


async def credit_deposit(
    tid: str, amount: float, transaction_id: str, req_key: Optional[str] = None
) -> bool:
    if transaction_id in _processed_deposits:
        return False
    if db.reference(f"Deposit_Done/{transaction_id}").get():
        return False

    def _add(cur):
        return round(float(cur or 0) + float(amount), 2)

    uref(tid).child("balance").transaction(_add)
    uref(tid).child("total_deposit").transaction(_add)
    uref(tid).update({"hasFirstDeposit": True})
    db.reference(f"Deposit_Done/{transaction_id}").set(
        {
            "telegram_id": tid,
            "amount": amount,
            "at": int(time.time() * 1000),
        }
    )
    if req_key:
        db.reference(f"Deposit_Requests/{req_key}").update(
            {
                "status": "approved",
                "transaction_id": transaction_id,
                "approvedAt": int(time.time() * 1000),
            }
        )
    else:
        db.reference("Deposit_Requests").push(
            {
                "telegram_id": tid,
                "amount": amount,
                "status": "approved",
                "transaction_id": transaction_id,
                "createdAt": int(time.time() * 1000),
                "approvedAt": int(time.time() * 1000),
            }
        )
    _processed_deposits.add(transaction_id)
    return True


async def deposit_commands_verify(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.effective_user or not update.message:
        return
    parts = (update.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "ডিপোজিট ভেরিফাই:\n/verifydep TRANSACTION_ID"
        )
        return
    txid = parts[1].strip()
    data = rupantor_verify(txid)
    if not data:
        await update.message.reply_text("Verify failed (network).")
        return
    status = str(data.get("status") or "").upper()
    if status != "COMPLETED":
        await update.message.reply_text(f"Status: {status or data}")
        return
    meta = data.get("metadata") or data.get("meta_data") or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    tid = str(meta.get("telegram_id") or update.effective_user.id)
    amount = float(data.get("amount") or 0)
    ok = await credit_deposit(tid, amount, txid)
    if ok:
        await update.message.reply_text(f"✅ Deposit +{amount} X\nTx: {txid}")
        try:
            if str(tid) != str(update.effective_user.id):
                await context.bot.send_message(
                    chat_id=int(tid), text=f"✅ Pocket X: Deposit {amount} X approved."
                )
        except Exception:
            pass
    else:
        await update.message.reply_text("Already credited or error.")


async def admin_approve_dep(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    if not update.effective_user or update.effective_user.id not in ADMIN_IDS:
        return
    parts = (update.message.text or "").split()
    if len(parts) < 4:
        await update.message.reply_text(
            "Usage: /approvedep <telegram_id> <amount> <transaction_id>"
        )
        return
    tid, amount_s, txid = parts[1], parts[2], parts[3]
    ok = await credit_deposit(tid, float(amount_s), txid)
    await update.message.reply_text("OK credited" if ok else "Fail/duplicate")


# ===================== BONUS =====================
async def bonus_loop(app: Application) -> None:
    while True:
        try:
            claims = db.reference("Bonus_Claims").get() or {}
            if isinstance(claims, dict):
                for key, row in list(claims.items()):
                    if not isinstance(row, dict):
                        continue
                    if row.get("status") != "pending" or key in _processed_bonus:
                        continue
                    await process_bonus_claim(app, key, row)
        except Exception as e:
            log.exception("bonus_loop: %s", e)
        await asyncio.sleep(2)


async def process_bonus_claim(
    app: Application, key: str, row: Dict[str, Any]
) -> None:
    tid = str(row.get("telegram_id") or "")
    btype = str(row.get("type") or "")
    if not tid:
        return
    if btype == "referral":
        db.reference(f"Bonus_Claims/{key}").update(
            {
                "status": "link_only",
                "note": "Open reference bot link",
                "processedAt": int(time.time() * 1000),
            }
        )
        _processed_bonus.add(key)
        return

    user = uref(tid).get() or {}
    claimed = user.get("claimed_bonuses") or {}
    code = str(row.get("code") or btype)
    if claimed.get(code):
        db.reference(f"Bonus_Claims/{key}").update(
            {"status": "rejected", "reason": "already_claimed"}
        )
        _processed_bonus.add(key)
        return

    amount = 0.0
    if btype == "weekly" or code == "WEEKLY150":
        amount = 150.0
    elif btype == "monthly" or code == "MONTHLY1000":
        amount = 1000.0
    elif btype == "deposit":
        tier_map = {
            "DEP100": 100,
            "DEP200": 130,
            "DEP400": 150,
            "DEP500": 200,
            "DEP1000": 300,
            "DEP1500": 400,
        }
        amount = float(tier_map.get(code, 0))
        if not user.get("hasFirstDeposit") and float(user.get("total_deposit") or 0) <= 0:
            db.reference(f"Bonus_Claims/{key}").update(
                {"status": "rejected", "reason": "no_deposit"}
            )
            _processed_bonus.add(key)
            return
    elif btype == "cashback":
        amount = float(row.get("preview") or 0)
        if amount <= 0:
            db.reference(f"Bonus_Claims/{key}").update(
                {"status": "rejected", "reason": "no_amount"}
            )
            _processed_bonus.add(key)
            return
    else:
        db.reference(f"Bonus_Claims/{key}").update(
            {"status": "rejected", "reason": "unknown_type"}
        )
        _processed_bonus.add(key)
        return

    if amount <= 0:
        db.reference(f"Bonus_Claims/{key}").update(
            {"status": "rejected", "reason": "zero"}
        )
        _processed_bonus.add(key)
        return

    def _add(c):
        return round(float(c or 0) + amount, 2)

    uref(tid).child("balance").transaction(_add)
    uref(tid).child("claimed_bonuses").child(code).set(True)
    db.reference(f"Bonus_Claims/{key}").update(
        {
            "status": "approved",
            "paid": amount,
            "processedAt": int(time.time() * 1000),
        }
    )
    _processed_bonus.add(key)
    try:
        await app.bot.send_message(
            chat_id=int(tid), text=f"🎁 Bonus +{amount} X ({code})"
        )
    except Exception:
        pass


# ===================== START MESSAGE =====================
async def send_saved_start_message(bot, chat_id: int) -> bool:
    """Send admin-configured start message (text/photo/video)."""
    try:
        cfg = db.reference("Bot_Settings/start_message").get() or {}
    except Exception as e:
        log.warning("start_message read: %s", e)
        return False
    if not cfg:
        return False
    try:
        kind = cfg.get("type") or "text"
        if kind == "photo" and cfg.get("file_id"):
            await bot.send_photo(
                chat_id=chat_id,
                photo=cfg["file_id"],
                caption=cfg.get("caption") or None,
            )
        elif kind == "video" and cfg.get("file_id"):
            await bot.send_video(
                chat_id=chat_id,
                video=cfg["file_id"],
                caption=cfg.get("caption") or None,
            )
        elif kind == "document" and cfg.get("file_id"):
            await bot.send_document(
                chat_id=chat_id,
                document=cfg["file_id"],
                caption=cfg.get("caption") or None,
            )
        elif cfg.get("text"):
            await bot.send_message(chat_id=chat_id, text=cfg["text"])
        else:
            return False
        return True
    except Exception as e:
        log.warning("send start message: %s", e)
        return False


# ===================== ADMIN / COMMANDS =====================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    if not u or not update.message:
        return
    # referral deep link
    if context.args:
        ref = context.args[0].strip()
        tid = str(u.id)
        try:
            user = uref(tid).get()
            if not user:
                ref_ok = bool(ref.isdigit() and uref(ref).get())
                uref(tid).set(
                    {
                        "telegram_id": tid,
                        "balance": 0,
                        "demo_balance": 10000,
                        "created_at": int(time.time() * 1000),
                        "referred_by": ref if ref_ok else None,
                        "reference_locked": bool(ref_ok),
                    }
                )
            elif not (user.get("referred_by") or user.get("reference_locked")):
                if ref.isdigit() and uref(ref).get():
                    uref(tid).update(
                        {"referred_by": ref, "reference_locked": True}
                    )
        except Exception as e:
            log.warning("start referral: %s", e)

    # custom start message first
    sent = await send_saved_start_message(context.bot, u.id)
    if not sent:
        await update.message.reply_text(
            "স্বাগতম Pocket X বটে।\n"
            "Mini App থেকে ট্রেড করুন।\n"
            "ডিপোজিটের পর: /verifydep TRANSACTION_ID"
        )


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_admin(update.effective_user.id):
        if update.message:
            await update.message.reply_text("Unauthorized")
        return
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔔 Notification", callback_data="adm_notify"),
                InlineKeyboardButton("📈 Today's Profit", callback_data="adm_profit"),
            ],
            [
                InlineKeyboardButton(
                    "💬 Start Message", callback_data="adm_start_msg"
                ),
            ],
        ]
    )
    await update.message.reply_text("Admin panel", reply_markup=kb)


async def admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    q = update.callback_query
    await q.answer()
    if not update.effective_user or not is_admin(update.effective_user.id):
        return ConversationHandler.END

    if q.data == "adm_profit":
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        try:
            data = db.reference(f"Today_Profit/{day}").get() or {}
        except Exception as e:
            await q.edit_message_text(f"Firebase error: {e}")
            return ConversationHandler.END
        await q.edit_message_text(
            f"📅 {day} (UTC)\n"
            f"Wins: {data.get('wins') or 0}\n"
            f"Total payouts: {data.get('total_payouts') or 0} X"
        )
        return ConversationHandler.END

    if q.data == "adm_start_msg":
        context.user_data["await_start_msg"] = True
        await q.edit_message_text(
            "Start Message সেট করুন:\n"
            "এখন ছবি / ভিডিও / টেক্সট পাঠান।\n"
            "মুছতে: /clear_start\n"
            "বাতিল: /cancel"
        )
        return START_MSG_WAIT

    if q.data == "adm_notify":
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("All users", callback_data="adm_n_all"),
                    InlineKeyboardButton("Personal user", callback_data="adm_n_one"),
                ]
            ]
        )
        await q.edit_message_text("Send notification to:", reply_markup=kb)
        return NOTIFY_CHOOSE

    if q.data == "adm_n_all":
        context.user_data["notify_mode"] = "all"
        await q.edit_message_text(
            "মেসেজ পাঠান (টেক্সট/ছবি/ভিডিও)। সব ইউজার আইডিতে যাবে।"
        )
        return NOTIFY_MESSAGE

    if q.data == "adm_n_one":
        context.user_data["notify_mode"] = "one"
        await q.edit_message_text("টার্গেট Telegram user id (শুধু সংখ্যা):")
        return NOTIFY_USER_ID

    return ConversationHandler.END


async def admin_start_msg_save(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.effective_user or not is_admin(update.effective_user.id):
        return ConversationHandler.END
    msg = update.message
    payload: Dict[str, Any] = {
        "updatedAt": int(time.time() * 1000),
        "updatedBy": update.effective_user.id,
    }
    if msg.photo:
        payload["type"] = "photo"
        payload["file_id"] = msg.photo[-1].file_id
        payload["caption"] = msg.caption or ""
    elif msg.video:
        payload["type"] = "video"
        payload["file_id"] = msg.video.file_id
        payload["caption"] = msg.caption or ""
    elif msg.document:
        payload["type"] = "document"
        payload["file_id"] = msg.document.file_id
        payload["caption"] = msg.caption or ""
    elif msg.text:
        payload["type"] = "text"
        payload["text"] = msg.text
    else:
        await msg.reply_text("টেক্সট/ছবি/ভিডিও পাঠান।")
        return START_MSG_WAIT

    try:
        db.reference("Bot_Settings/start_message").set(payload)
        await msg.reply_text("✅ Start Message সেভ হয়েছে। /start দিয়ে টেস্ট করুন।")
    except Exception as e:
        await msg.reply_text(f"Save failed: {e}")
    context.user_data.pop("await_start_msg", None)
    return ConversationHandler.END


async def cmd_clear_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not is_admin(update.effective_user.id):
        return
    try:
        db.reference("Bot_Settings/start_message").delete()
        await update.message.reply_text("Start Message মুছে ফেলা হয়েছে।")
    except Exception as e:
        await update.message.reply_text(str(e))


async def admin_notify_uid(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = (update.message.text or "").strip()
    if not text.isdigit():
        await update.message.reply_text("Invalid id. শুধু সংখ্যা পাঠান:")
        return NOTIFY_USER_ID
    context.user_data["notify_uid"] = int(text)
    await update.message.reply_text("এখন মেসেজ পাঠান:")
    return NOTIFY_MESSAGE


async def admin_notify_msg(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    mode = context.user_data.get("notify_mode")
    try:
        if mode == "one":
            uid = context.user_data.get("notify_uid")
            await context.bot.copy_message(
                chat_id=uid,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
            )
            await update.message.reply_text(f"Sent to {uid}")
        else:
            try:
                ids = list_user_telegram_ids()
            except Exception as e:
                await update.message.reply_text(
                    f"Firebase users read failed:\n{e}\n"
                    "Service account / JWT চেক করুন।"
                )
                return ConversationHandler.END
            n_ok, n_fail = 0, 0
            for tid in ids:
                try:
                    await context.bot.copy_message(
                        chat_id=tid,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id,
                    )
                    n_ok += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    n_fail += 1
            await update.message.reply_text(
                f"Broadcast done. users={len(ids)} OK={n_ok} fail={n_fail}"
            )
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    if update.message:
        await update.message.reply_text("Cancelled", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ===================== MAIN =====================
async def post_init(app: Application) -> None:
    app.create_task(market_loop(app))
    app.create_task(trade_intake_loop(app))
    app.create_task(otp_loop(app))
    app.create_task(bonus_loop(app))
    log.info("Background loops started")


def main() -> None:
    init_firebase()
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("verifydep", deposit_commands_verify))
    app.add_handler(CommandHandler("approvedep", admin_approve_dep))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("Admin", cmd_admin))
    app.add_handler(CommandHandler("clear_start", cmd_clear_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_cb, pattern=r"^adm_")],
        states={
            NOTIFY_CHOOSE: [CallbackQueryHandler(admin_cb, pattern=r"^adm_")],
            NOTIFY_USER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_notify_uid)
            ],
            NOTIFY_MESSAGE: [
                MessageHandler(
                    (
                        filters.TEXT
                        | filters.PHOTO
                        | filters.VIDEO
                        | filters.Document.ALL
                    )
                    & ~filters.COMMAND,
                    admin_notify_msg,
                )
            ],
            START_MSG_WAIT: [
                MessageHandler(
                    (
                        filters.TEXT
                        | filters.PHOTO
                        | filters.VIDEO
                        | filters.Document.ALL
                    )
                    & ~filters.COMMAND,
                    admin_start_msg_save,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_cb, pattern=r"^adm_"))

    log.info("Bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
