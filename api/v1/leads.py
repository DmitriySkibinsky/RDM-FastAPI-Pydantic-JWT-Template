from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Query
)

from api.v1.form_token import get_form_token_service
from core.dependencies import get_current_admin
from db.models import Lead
from db.session import get_db_session
from schemas.leads import LeadCreate, LeadResponse, LeadsListResponse
from services.form_token.exceptions import (
    FormTokenNotFoundError,
    InvalidFormTokenDataError
)
from services.form_token.service import FormTokenService
from services.leads.exceptions import LeadCreationError, LeadNotFoundError
from services.leads.service import LeadService


router = APIRouter()


def get_lead_service(session=Depends(get_db_session)) -> LeadService:
    return LeadService(session)


@router.post(
    "/leads",
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой заявки",
    description=(
        "Создаёт новую заявку (lead) от клиента в системе.\n\n"
        "### Процесс создания:\n"
        "1. Данные валидируются по схеме LeadCreate\n"
        "2. Проверяется корректность email формата\n"
        "3. Заявка сохраняется в базу данных\n"
        "4. Автоматически проставляется дата создания (UTC)\n\n"
        "### Особенности:\n"
        "- Все текстовые поля поддерживают Unicode символы\n"
        "- Email проходит строгую валидацию формата\n"
        "- Данные безопасно экранируются от SQL-инъекций\n"
        "- При ошибке сохранения выполняется откат транзакции"
    ),
    responses={
        201: {
            "description": "Заявка успешно создана",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Заявка успешно принята",
                        "lead_id": 123,
                    }
                }
            },
        },
        422: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email",
                            }
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Ошибка: connection to database failed"
                    }
                }
            },
        },
    },
    tags=["Заявки"],
    operation_id="create_lead",
)
async def create_lead(
    lead_data: LeadCreate,
    background_tasks: BackgroundTasks,
    lead_service: LeadService = Depends(get_lead_service),
    token_service: FormTokenService = Depends(get_form_token_service),
) -> dict:

    try:
        await token_service.verify_token(lead_data.token)
    except (FormTokenNotFoundError, InvalidFormTokenDataError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недействительный токен формы: {str(e)}"
        )

    try:
        return await lead_service.create_lead(lead_data, background_tasks)
    except LeadCreationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get(
    "/leads",
    response_model=LeadsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение списка всех заявок",
    description=(
            "Возвращает список всех заявок с пагинацией и сортировкой.\n\n"
            "### Особенности:\n"
            "- Доступно только администраторам\n"
            "- Сортировка по дате создания (сначала новые)\n"
            "- Поддержка пагинации через параметры skip и limit\n"
            "- Возвращает общее количество заявок для построения пагинации на фронтенде\n"
            "- Можно фильтровать только активные заявки (status=1)"
    ),
    responses={
        200: {
            "description": "Успешный ответ со списком заявок",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "name": "Иван Петров",
                                "email": "ivan@example.com",
                                "phone": "+79001234567",
                                "subject": "Вопрос по услугам",
                                "message": "Здравствуйте, хотел бы узнать подробнее...",
                                "date_created": "2024-01-15T10:30:00",
                                "status": 1
                            }
                        ],
                        "total": 45,
                        "skip": 0,
                        "limit": 10
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated"}
                }
            },
        },
        403: {
            "description": "Доступ запрещен (не администратор)",
            "content": {
                "application/json": {
                    "example": {"detail": "You do not have permission to access this resource"}
                }
            },
        },
    },
    tags=["Заявки"],
    operation_id="get_leads",
)
async def get_leads(
        _admin=Depends(get_current_admin),
        service: LeadService = Depends(get_lead_service),
        skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
        limit: int = Query(10, ge=1, le=100, description="Размер страницы (макс. 100)"),
        active_only: bool = Query(True, description="Только активные заявки"),
) -> LeadsListResponse:
    """
    Получение списка всех заявок с пагинацией.
    Доступно только администраторам.
    """
    try:
        items = await service.get_all_leads(
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

        total = await service.count_leads(active_only=active_only)

        return LeadsListResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка получения списка заявок: {str(e)}"
        )


@router.get(
    "/leads/{lead_id}",
    response_model=LeadResponse,
    status_code=status.HTTP_200_OK,
    summary="Получение заявки по ID",
    description="Возвращает детальную информацию по конкретной заявке",
    responses={
        200: {
            "description": "Заявка найдена",
        },
        404: {
            "description": "Заявка не найдена",
            "content": {
                "application/json": {
                    "example": {"detail": "Lead not found"}
                }
            },
        },
    },
    tags=["Заявки"],
    operation_id="get_lead_by_id",
)
async def get_lead_by_id(
    lead_id: int,
    _admin=Depends(get_current_admin),
    service: LeadService = Depends(get_lead_service),
) -> Lead:
    """
    Получение детальной информации по конкретной заявке.
    Доступно только администраторам.
    """
    try:
        lead = await service.get_by_id(lead_id, active_only=False)
        return lead
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
