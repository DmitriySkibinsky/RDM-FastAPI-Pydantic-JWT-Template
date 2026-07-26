import hashlib
from datetime import timedelta

from redis.asyncio import Redis

from services.form_token.exceptions import (
    FormTokenNotFoundError,
    InvalidFormTokenDataError
)


def hash_form_token(token: str) -> str:
    if not token:
        raise ValueError("Токен не может быть пустым")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class FormTokenService:
    HASH_LENGTH = 64

    def __init__(self, redis: Redis):
        self.redis = redis
        self.ttl = timedelta(hours=1)

    async def register_token(self, form_token: str) -> str:
        """
        Принимает оригинальный токен формы,
        вычисляет хеш и сохраняет его в Redis со значением '1' на 1 час.

        Возвращает хешированный токен (hex-строку).
        """
        hashed = hash_form_token(form_token)

        await self.redis.setex(
            name=hashed,
            time=self.ttl,
            value="1"
        )

        return hashed

    async def verify_token(self, form_token: str) -> dict:
        """
        Принимает оригинальный токен формы,
        вычисляет его хеш и проверяет наличие в Redis.

        Возвращает информацию о токене или поднимает исключение.
        """
        if not form_token:
            raise InvalidFormTokenDataError("Токен формы не передан")

        hashed_token = hash_form_token(form_token)

        if len(hashed_token) != self.HASH_LENGTH:
            raise InvalidFormTokenDataError(
                f"Внутренняя ошибка: некорректная длина "
                f"хеша ({len(hashed_token)} символов)"
            )

        value = await self.redis.get(hashed_token)

        if value is None:
            raise FormTokenNotFoundError("Токен не найден или истёк")

        if value != b"1" and value != "1":
            raise InvalidFormTokenDataError("Повреждённые данные токена")

        ttl = await self.redis.ttl(hashed_token)

        return {
            "valid": True,
            "expires_in_seconds": ttl if ttl >= 0 else 0,
            "hashed_token": hashed_token,
        }
