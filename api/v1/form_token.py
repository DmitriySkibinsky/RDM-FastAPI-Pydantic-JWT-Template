from fastapi import APIRouter, Depends, HTTPException, Request, status

from core.config import settings
from core.dependencies import get_current_admin
from schemas.tokens import FormTokenCreate
from services.form_token.service import FormTokenService
from services.form_token.exceptions import (
    FormTokenNotFoundError,
    InvalidFormTokenDataError,
)

router = APIRouter(prefix="/form_tokens", tags=["form-tokens"])


def get_form_token_service(
    request: Request,
) -> FormTokenService:
    redis = request.app.state.redis
    if redis is None:
        raise RuntimeError("Redis клиент не инициализирован в app.state")
    return FormTokenService(redis)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Сохраняет хеш form_token как ключ в Redis со значением '1' на 1 час"
)
async def register_form_token_hash(
    data: FormTokenCreate,
    service: FormTokenService = Depends(get_form_token_service),
):
    if data.nuxt_auth_token != settings.nuxt_auth_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный nuxt_auth_token"
        )

    try:
        hashed_token = await service.register_token(data.form_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка регистрации токена: {str(e)}"
        )

    return {
        "status": "registered",
        "hashed_token": hashed_token,
        "expires_in": "1 hour"
    }


@router.get(
    "/{hashed_token}",
    summary="Проверяет существование токена по его хешу (только для администраторов)",
    response_model=dict
)
async def check_form_token(
    hashed_token: str,
    _admin=Depends(get_current_admin),
    service: FormTokenService = Depends(get_form_token_service),
):
    try:
        result = await service.verify_token(hashed_token)
        return result
    except FormTokenNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidFormTokenDataError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка проверки токена: {str(e)}"
        )
