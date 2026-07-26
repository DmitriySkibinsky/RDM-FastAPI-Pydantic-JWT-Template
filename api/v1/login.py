from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from db.session import get_db_session
from schemas.auth import UserLogin, UserOut
from schemas.user import UserCreate
from services.auth.exceptions import (
    UsernameAlreadyExistsError,
    UserNotFoundError,
    InvalidPasswordError
)
from services.auth.service import AuthService


router = APIRouter()


def get_auth_service(session=Depends(get_db_session)) -> AuthService:
    return AuthService(session)


@router.post(
    "/register",
    response_model=UserOut,
    summary="Регистрация нового пользователя",
    description=(
        "Создаёт нового пользователя в системе.\n\n"
        "Требования к паролю проверяются на стороне клиента.\n"
        "Имя пользователя должно быть уникальным."
    ),
    response_description="Данные созданного пользователя (без пароля)",
    responses={
        400: {
            "description": "Пользователь с таким именем уже существует",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Пользователь с таким именем уже существует"
                    }
                }
            },
        },
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserOut:
    try:
        return await service.register(user_data)
    except UsernameAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/login",
    response_model=dict,
    summary="Аутентификация пользователя",
    description=(
        "Проверяет учетные данные и возвращает JWT-токен доступа.\n\n"
        "Используется схема Bearer Token.\n"
        "Токен имеет ограниченное время жизни."
    ),
    response_description="JWT-токен и основная информация о пользователе",
    responses={
        401: {
            "description": "Неверные учетные данные",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Неверное имя пользователя или пароль"
                    }
                }
            },
        },
        422: {"description": "Ошибка валидации входных данных"},
    },
)
@router.post("/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    user_login = UserLogin(
        username=form_data.username, password=form_data.password
    )
    try:
        token_data = await service.login(user_login)
    except UserNotFoundError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except InvalidPasswordError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return {"access_token": token_data.access_token, "token_type": "bearer"}
