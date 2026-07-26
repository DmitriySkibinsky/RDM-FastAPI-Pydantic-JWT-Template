from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from api.utils.key_builder import query_aware_key_builder
from core.dependencies import get_current_admin
from db.models import Question
from db.session import get_db_session
from schemas.questions import QuestionCreate, QuestionOut, QuestionUpdate
from services.questions.service import QuestionService
from services.questions.exceptions import (
    NothingToUpdateError,
    QuestionAlreadyExistsError,
    QuestionNotActiveError,
    QuestionNotFoundError,
)


router = APIRouter(prefix="/questions", tags=["FAQ"])


def get_question_service(session: AsyncSession = Depends(get_db_session)):
    return QuestionService(session)


@router.get(
    "",
    response_model=list[QuestionOut],
    summary="Список всех активных вопросов (FAQ)",
    description=("Возвращает все опубликованные вопросы, "
                 "отсортированные от новых к старым."),
    responses={200: {"description": "Список активных вопросов FAQ"}},
)
@cache(expire=300,
       namespace="questions:list",
       key_builder=query_aware_key_builder
)
async def get_all_active_questions(
    service: QuestionService = Depends(get_question_service),
):
    questions = await service.get_all_active(
        order_by=Question.id.desc()
    )
    return [QuestionOut.model_validate(q) for q in questions]


@router.get(
    "/{question_id}",
    response_model=QuestionOut,
    summary="Информация об одном вопросе",
    description=("Возвращает полный текст вопроса и ответа по его ID. "
                 "Доступны только активные вопросы."),
    responses={
        200: {"description": "Детальная информация о вопросе"},
        404: {"description": "Вопрос не найден"},
        410: {"description": "Вопрос архивирован"},
    },
)
@cache(expire=300,
       namespace="questions:detail",
       key_builder=query_aware_key_builder
)
async def get_question(
    question_id: int,
    service: QuestionService = Depends(get_question_service),
):
    try:
        question = await service.get_by_id(question_id)
        return QuestionOut.model_validate(question)
    except QuestionNotFoundError:
        raise HTTPException(404, "Вопрос не найден")
    except QuestionNotActiveError:
        raise HTTPException(410, "Вопрос архивирован")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )


@router.post(
    "",
    response_model=QuestionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового вопроса (FAQ)",
    description=(
        "Создаёт новую запись вопроса в системе.\n\n"
        "**Доступ:** только администраторы\n"
        "Вопрос сразу создаётся в статусе «активен» (status=1)."
    ),
    responses={
        201: {"description": "Вопрос успешно создан"},
        400: {"description": "Вопрос с таким заголовком уже существует"},
        401: {"description": "Требуется авторизация администратора"},
        422: {"description": "Ошибка валидации данных"},
    },
)
async def create_question(
    data: QuestionCreate,
    current_admin=Depends(get_current_admin),
    service: QuestionService = Depends(get_question_service),
):
    try:
        question = await service.create_question(data)
        await FastAPICache.clear(namespace="questions")
        return QuestionOut.model_validate(question)
    except QuestionAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )


@router.put(
    "/{question_id}",
    response_model=QuestionOut,
    summary="Обновление вопроса",
    description=(
        "Частичное обновление данных вопроса.\n"
        "Обновляются только переданные поля.\n"
        "**Доступ:** только администраторы\n"
        "Нельзя редактировать архивированные вопросы."
    ),
    responses={
        200: {"description": "Вопрос успешно обновлён"},
        400: {"description": "Не переданы поля для обновления"},
        401: {"description": "Требуется авторизация администратора"},
        404: {"description": "Вопрос не найден"},
        410: {"description": "Нельзя редактировать архивированный вопрос"},
        422: {"description": "Ошибка валидации данных"},
    },
)
async def update_question(
    question_id: int,
    data: QuestionUpdate,
    current_admin=Depends(get_current_admin),
    service: QuestionService = Depends(get_question_service),
):
    try:
        q = await service.update(question_id, **data.model_dump(exclude_unset=True))
        await FastAPICache.clear(namespace="questions")
        return QuestionOut.model_validate(q)
    except QuestionNotFoundError:
        raise HTTPException(404, "Вопрос не найден")
    except QuestionNotActiveError:
        raise HTTPException(410, "Нельзя редактировать архивированный вопрос")
    except NothingToUpdateError:
        raise HTTPException(400, "Не переданы поля для обновления")


@router.delete(
    "/{question_id}",
    summary="Удаление (архивирование) вопроса",
    description=(
        "Выполняет мягкое удаление вопроса — устанавливает status=0.\n\n"
        "**Доступ:** только администраторы\n"
        "Вопрос остаётся в базе, его можно восстановить.\n"
        "После удаления вопрос перестаёт отображаться "
        "в списках и по прямой ссылке."
    ),
    responses={
        200: {"description": "Вопрос успешно архивирован"},
        401: {"description": "Требуется авторизация администратора"},
        404: {"description": "Вопрос не найден"},
        410: {"description": "Вопрос уже архивирован"},
    },
)
async def archive_question(
    question_id: int,
    current_admin=Depends(get_current_admin),
    service: QuestionService = Depends(get_question_service),
):
    try:
        archived = await service.archive(question_id)
        await FastAPICache.clear(namespace="questions")
        return {
            "message": "Вопрос успешно архивирован",
            "question_id": question_id,
            "title": archived.title,
        }
    except QuestionNotFoundError:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    except QuestionNotActiveError as e:
        raise HTTPException(status_code=410, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при архивировании вопроса: {str(e)}"
        )
