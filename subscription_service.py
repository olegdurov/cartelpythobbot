"""
bot/services/subscription_service.py
"""
from datetime import datetime, timedelta, timezone


async def has_active_subscription(db, user_id: int) -> bool:
    row = await db.fetchrow(
        """
        SELECT 1 FROM subscriptions
        WHERE  user_id = $1 AND status = 'active' AND expires_at > NOW()
        """,
        user_id,
    )
    return row is not None


async def get_subscription_info(db, user_id: int):
    return await db.fetchrow(
        """
        SELECT * FROM subscriptions
        WHERE  user_id = $1
        ORDER  BY created_at DESC
        LIMIT  1
        """,
        user_id,
    )


async def create_subscription(
    db, user_id: int, provider: str, pay_ref: str | None = None
) -> None:
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    # Expire any previous active subs
    await db.execute(
        "UPDATE subscriptions SET status = 'expired' WHERE user_id = $1 AND status = 'active'",
        user_id,
    )
    await db.execute(
        """
        INSERT INTO subscriptions (user_id, expires_at, payment_provider, payment_ref)
        VALUES ($1, $2, $3, $4)
        """,
        user_id, expires, provider, pay_ref,
    )


async def expire_stale_subscriptions(db) -> int:
    """Call from a daily scheduler job."""
    result = await db.execute(
        """
        UPDATE subscriptions
        SET    status = 'expired'
        WHERE  status = 'active' AND expires_at < NOW()
        """
    )
    # Returns e.g. "UPDATE 3"
    return int(result.split()[-1])
