from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import create_access_token, hash_password, verify_password
from db.models import User
from schemas.auth import Token, UserLogin, UserOut
from schemas.user import UserCreate
from services.auth.exceptions import (
    InvalidPasswordError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user_by_username(
        self, username: str, raise_if_not_found: bool = True
    ) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        user = result.scalars().first()

        if not user and raise_if_not_found:
            raise UserNotFoundError()

        return user

    async def register(self, data: UserCreate) -> UserOut:
        # Проверка уникальности
        if await self._get_user_by_username(
            data.username, raise_if_not_found=False
        ):
            raise UsernameAlreadyExistsError(data.username)

        hashed_password = hash_password(data.password)

        user = User(
            username=data.username,
            password=hashed_password,
            role=1,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return UserOut.model_validate(user)

    async def login(self, user_data: UserLogin) -> Token:

        user = await self._get_user_by_username(
            user_data.username, raise_if_not_found=False
        )
        if not user:
            raise UserNotFoundError()

        # Затем проверяем пароль
        if not verify_password(user_data.password, user.password):
            raise InvalidPasswordError()

        access_token = create_access_token(data={"sub": user.username})

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            username=user.username,
        )
