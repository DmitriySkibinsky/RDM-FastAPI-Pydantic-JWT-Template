from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from api.utils.key_builder import query_aware_key_builder
from core.dependencies import get_current_admin
from db.models import News
from db.session import get_db_session
from schemas.news import NewsArchiveResponse, NewsCreate, NewsOut, NewsUpdate
from services.news.service import NewsService
from services.news.exceptions import (
    NewsNotActiveError,
    NewsNotFoundError,
    NothingToUpdateError,
)


router = APIRouter(prefix="/news")


def get_news_service(session=Depends(get_db_session)) -> NewsService:
    return NewsService(session)


@router.get(
    "",
    response_model=list[NewsOut],
    summary="Список всех активных новостей",
    description=(
        "Возвращает все опубликованные новости, "
        "отсортированные от новых к старым"
    ),
    responses={500: {"description": "Ошибка сервера при получении списка"}},
)
@cache(expire=300,
       namespace="news:list",
       key_builder=query_aware_key_builder
)
async def get_active_news_list(service: NewsService = Depends(get_news_service)):
    items = await service.get_all_active(order_by=News.created_at.desc())
    return [NewsOut.model_validate(item) for item in items]


@router.get(
    "/{news_id}",
    response_model=NewsOut,
    summary="Получить новость по ID",
    description="Возвращает полную информацию об одной активной новости",
    responses={
        404: {"description": "Новость не найдена"},
        410: {"description": "Новость архивирована или удалена"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
@cache(expire=180,
       namespace="news:detail",
       key_builder=query_aware_key_builder
)
async def get_news_by_id(
    news_id: int,
    service: NewsService = Depends(get_news_service),
):
    try:
        news = await service.get_by_id(news_id)
        return NewsOut.model_validate(news)
    except NewsNotFoundError:
        raise HTTPException(404, "Новость не найдена")
    except NewsNotActiveError:
        raise HTTPException(410, "Новость архивирована или удалена")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )

@router.post(
    "",
    response_model=NewsOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создание новой новости",
    description=(
        "Создаёт новую новость в системе.\n\n"
        "Доступ **только для администраторов**.\n"
        "Новая новость автоматически получает статус `1` (опубликована)."
    ),
    responses={
        201: {"description": "Новость успешно создана"},
        400: {"description": "Ошибка валидации или некорректные данные"},
        401: {"description": "Необходима авторизация администратора"},
        422: {"description": "Ошибка валидации входных данных (Pydantic)"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def create_news(
    data: NewsCreate,
    _admin=Depends(get_current_admin),
    service: NewsService = Depends(get_news_service),
):
    news = await service.create(title=data.title, text=data.text)
    await FastAPICache.clear(namespace="news")
    return NewsOut.model_validate(news)


@router.put(
    "/{news_id}",
    response_model=NewsOut,
    summary="Обновление новости",
    description=(
        "Частичное обновление информации о новости.\n\n"
        "Обновляются только те поля, которые были переданы в запросе.\n"
        "Доступ **только для администраторов**.\n"
        "Нельзя обновлять архивированные или удалённые новости (status ≠ 1)."
    ),
    responses={
        200: {"description": "Новость успешно обновлена"},
        400: {"description": "Не переданы поля для обновления"},
        401: {"description": "Необходима авторизация администратора"},
        404: {"description": "Новость не найдена"},
        410: {
            "description": "Нельзя редактировать архивированную или удалённую новость"
        },
        422: {"description": "Ошибка валидации входных данных"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def update_news(
    news_id: int,
    data: NewsUpdate,
    _admin=Depends(get_current_admin),
    service: NewsService = Depends(get_news_service),
):
    update_dict = data.model_dump(exclude_unset=True)
    if "title" in update_dict:
        update_dict["title"] = update_dict["title"].strip()
    if "text" in update_dict:
        update_dict["text"] = update_dict["text"].strip()

    try:
        news = await service.update(news_id, **update_dict)
        await FastAPICache.clear(namespace="news")
        return NewsOut.model_validate(news)
    except NewsNotFoundError:
        raise HTTPException(404, "Новость не найдена")
    except NewsNotActiveError:
        raise HTTPException(410, "Нельзя редактировать архивированную новость")
    except NothingToUpdateError:
        raise HTTPException(400, "Не передано ни одного поля для обновления")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )


@router.delete(
    "/{news_id}",
    response_model=NewsArchiveResponse,
    summary="Удаление (архивирование) новости",
    description=(
        "Выполняет мягкое удаление новости — меняет статус на `0`.\n\n"
        "Запись физически не удаляется из базы, её можно восстановить.\n"
        "После удаления новость перестаёт отображаться"
        " в списках и по прямой ссылке.\n"
        "Доступ **только для администраторов**."
    ),
    responses={
        200: {"description": "Новость успешно архивирована"},
        401: {"description": "Необходима авторизация администратора"},
        404: {"description": "Новость не найдена"},
        410: {"description": "Новость уже архивирована или удалена"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
async def archive_news(
    news_id: int,
    _admin=Depends(get_current_admin),
    service: NewsService = Depends(get_news_service),
):
    try:
        archived = await service.archive(news_id)
        await FastAPICache.clear(namespace="news")
        return NewsArchiveResponse(
            message="Новость успешно архивирована",
            news_id=news_id,
            title=archived.title,
            new_status=0,
        )
    except NewsNotFoundError:
        raise HTTPException(404, "Новость не найдена")
    except NewsNotActiveError as e:
        raise HTTPException(410, str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )
