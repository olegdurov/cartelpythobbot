"""
bot/services/user_service.py
"""
from __future__ import annotations


async def get_or_create_user(db, tg_user, referral_code: str | None = None):
    """Returns (user_row, is_new)."""
    row = await db.fetchrow("SELECT * FROM users WHERE id = $1", tg_user.id)
    if row:
        return row, False

    # Resolve referrer
    referrer_id = None
    if referral_code:
        ref_row = await db.fetchrow(
            "SELECT id FROM users WHERE referral_code = $1", referral_code
        )
        if ref_row and ref_row["id"] != tg_user.id:
            referrer_id = ref_row["id"]

    new_row = await db.fetchrow(
        """
        INSERT INTO users (id, username, full_name, referred_by)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        tg_user.id,
        tg_user.username,
        tg_user.full_name,
        referrer_id,
    )
    return new_row, True


async def get_user_lang(db, user_id: int) -> str:
    row = await db.fetchrow("SELECT language_code FROM users WHERE id = $1", user_id)
    return row["language_code"] if row else "en"
