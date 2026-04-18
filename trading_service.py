"""
bot/services/trading_service.py — Bridge between the bot and your Python algorithm.

Replace the RISK_PARAMS dict and the run_algorithm() call with your actual logic.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

# Risk level → parameter mapping passed to your algorithm
RISK_PARAMS: dict[int, dict] = {
    1: {"max_position_pct": 2,  "leverage": 1,  "sl_pct": 1.0, "tp_pct": 1.5},
    2: {"max_position_pct": 5,  "leverage": 2,  "sl_pct": 1.5, "tp_pct": 2.5},
    3: {"max_position_pct": 10, "leverage": 3,  "sl_pct": 2.0, "tp_pct": 4.0},
    4: {"max_position_pct": 20, "leverage": 5,  "sl_pct": 3.0, "tp_pct": 6.0},
    5: {"max_position_pct": 50, "leverage": 10, "sl_pct": 5.0, "tp_pct": 10.0},
}


async def set_risk_level(db, user_id: int, level: int) -> None:
    """Persist chosen risk level (stored in a simple user_settings JSON column or trades table)."""
    # Using a lightweight approach: store in users table extended field.
    # If you don't have a risk_level column yet, add:
    #   ALTER TABLE users ADD COLUMN risk_level SMALLINT NOT NULL DEFAULT 2;
    await db.execute(
        "UPDATE users SET risk_level = $1 WHERE id = $2",
        level, user_id,
    )
    logger.info("User %s set risk level to %s", user_id, level)


async def get_risk_level(db, user_id: int) -> int:
    row = await db.fetchrow("SELECT risk_level FROM users WHERE id = $1", user_id)
    return row["risk_level"] if row and row.get("risk_level") else 2


async def start_trading(db, user_id: int, exchange: str) -> None:
    """
    Called when the user activates trading.
    Loads their API keys, gets risk params, and hands off to your algorithm.
    """
    from bot.security.vault import load_api_keys
    import ccxt.async_support as ccxt_async

    api_key, api_secret = await load_api_keys(db, user_id, exchange)
    risk_level  = await get_risk_level(db, user_id)
    params      = RISK_PARAMS[risk_level]

    # ── Replace below with your actual algorithm import ──────────────────────
    # from algorithm.strategy import AlphaStrategy
    # strategy = AlphaStrategy(
    #     exchange   = exchange,
    #     api_key    = api_key,
    #     api_secret = api_secret,
    #     **params,
    # )
    # await strategy.run()
    # ─────────────────────────────────────────────────────────────────────────

    logger.info(
        "Trading started for user %s on %s | risk=%s params=%s",
        user_id, exchange, risk_level, params,
    )
