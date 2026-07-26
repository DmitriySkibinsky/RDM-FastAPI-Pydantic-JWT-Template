from fastapi import Depends, HTTPException
from fastapi import status as http_status

from core.security import get_current_user
from db.models import User


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Проверяет, что текущий пользователь — администратор
    """
    if current_user.role != 0:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешён только администраторам",
        )

    return current_user
