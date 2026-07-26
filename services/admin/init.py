import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from db.models import User


async def ensure_admin_exists(session: AsyncSession) -> None:
    admin_login = os.getenv("ADMIN_LOGIN")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_login or not admin_password:
        return

    result = await session.execute(
        select(User).where(User.username == admin_login)
    )
    admin = result.scalar_one_or_none()

    if admin:
        return

    new_admin = User(
        username=admin_login,
        password=hash_password(admin_password),
        role=0,
    )

    session.add(new_admin)
    await session.commit()
