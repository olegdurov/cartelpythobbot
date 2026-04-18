"""
bot/services/referral_service.py — 10% lifetime referral commission logic.
"""
import os

COMMISSION_PCT = float(os.environ.get("REFERRAL_COMMISSION_PCT", "10")) / 100


async def pay_referral_commission(db, referee_id: int, subscription_price: float) -> None:
    """
    If the user was referred, credit 10% of their payment to the referrer.
    Must be called inside the same transaction as create_subscription.
    """
    row = await db.fetchrow(
        "SELECT referred_by FROM users WHERE id = $1", referee_id
    )
    if not row or not row["referred_by"]:
        return

    referrer_id = row["referred_by"]
    commission  = round(subscription_price * COMMISSION_PCT, 4)

    # Get the subscription id that was just created
    sub = await db.fetchrow(
        "SELECT id FROM subscriptions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
        referee_id,
    )

    await db.execute(
        """
        INSERT INTO referral_payouts (referrer_id, referee_id, subscription_id, amount_usd)
        VALUES ($1, $2, $3, $4)
        """,
        referrer_id, referee_id, sub["id"], commission,
    )

    await db.execute(
        "UPDATE users SET referral_balance = referral_balance + $1 WHERE id = $2",
        commission, referrer_id,
    )
