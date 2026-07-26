from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from api.utils.key_builder import query_aware_key_builder
from core.dependencies import get_current_admin
from db.models import Project
from db.session import get_db_session
from schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from services.projects.service import ProjectService
from services.projects.exceptions import (
    NothingToUpdateError,
    ProjectNotActiveError,
    ProjectNotFoundError,
)


router = APIRouter(prefix="/projects")


def get_project_service(session: AsyncSession = Depends(get_db_session)):
    return ProjectService(session)


@router.get(
    "",
    response_model=list[ProjectOut],
    summary="Список всех активных проектов",
    description=("Возвращает все опубликованные проекты, "
                 "отсортированные от новых к старым (по дате создания)."),
    responses={200: {"description": "Список активных проектов"}},
)
@cache(expire=300,
       namespace="projects:list",
       key_builder=query_aware_key_builder
)
async def get_active_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ProjectService = Depends(get_project_service),
):
    items = await service.get_all_active(
        skip=skip, limit=limit, order_by=Project.date_created.desc()
    )
    return [ProjectOut.model_validate(p) for p in items]


@router.get(
    "/{project_id}",
    response_model=ProjectOut,
    summary="Информация об одном проекте",
    description=("Возвращает полные данные проекта по его ID. "
                 "Доступны только активные проекты."),
    responses={
        200: {"description": "Детальная информация о проекте"},
        404: {"description": "Проект не найден"},
        410: {"description": "Проект архивирован или удалён"},
    },
)
@cache(expire=180,
       namespace="projects:detail",
       key_builder=query_aware_key_builder
)
async def get_project_by_id(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
):
    try:
        project = await service.get_by_id(project_id)
        return ProjectOut.model_validate(project)
    except ProjectNotFoundError:
        raise HTTPException(404, "Проект не найден")
    except ProjectNotActiveError:
        raise HTTPException(410, "Проект архивирован или удалён")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового проекта",
    description=(
        "Создаёт новую запись проекта в системе.\n\n"
        "**Доступ:** только администраторы\n"
        "Проект сразу создаётся в статусе «активен» (status=1)."
    ),
    responses={
        201: {"description": "Проект успешно создан"},
        400: {"description": "Проект с таким названием уже существует"},
        401: {"description": "Требуется авторизация администратора"},
        422: {"description": "Ошибка валидации данных"},
    },
)
async def create_project(
    data: ProjectCreate,
    current_admin=Depends(get_current_admin),
    service: ProjectService = Depends(get_project_service),
):
    project = await service.create(**data.model_dump())
    await FastAPICache.clear(namespace="projects")
    return ProjectOut.model_validate(project)


@router.put(
    "/{project_id}",
    response_model=ProjectOut,
    summary="Обновление проекта",
    description=(
        "Частичное обновление данных проекта.\n"
        "Обновляются только переданные поля.\n"
        "**Доступ:** только администраторы\n"
        "Нельзя редактировать архивированные или удалённые проекты."
    ),
    responses={
        200: {"description": "Проект успешно обновлён"},
        400: {"description": "Не переданы поля для обновления"},
        401: {"description": "Требуется авторизация администратора"},
        404: {"description": "Проект не найден"},
        410: {
            "description": "Нельзя редактировать архивированный/удалённый проект"
        },
        422: {"description": "Ошибка валидации данных"},
    },
)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_admin=Depends(get_current_admin),
    service: ProjectService = Depends(get_project_service),
):
    try:
        p = await service.update(project_id, **data.model_dump(exclude_unset=True))
        await FastAPICache.clear(namespace="projects")
        return ProjectOut.model_validate(p)
    except ProjectNotFoundError:
        raise HTTPException(404, "Проект не найден")
    except ProjectNotActiveError:
        raise HTTPException(410, "Нельзя редактировать архивированный проект")
    except NothingToUpdateError:
        raise HTTPException(400, "Не переданы поля для обновления")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )


@router.delete(
    "/{project_id}",
    summary="Удаление (архивирование) проекта",
    description=(
        "Выполняет мягкое удаление проекта — устанавливает status=0.\n\n"
        "**Доступ:** только администраторы\n"
        "Проект остаётся в базе, его можно восстановить.\n"
        "После удаления проект перестаёт отображаться "
        "в списках и по прямой ссылке."
    ),
    responses={
        200: {"description": "Проект успешно архивирован"},
        401: {"description": "Требуется авторизация администратора"},
        404: {"description": "Проект не найден"},
        410: {"description": "Проект уже удалён"},
    },
)
async def archive_project(
    project_id: int,
    current_admin=Depends(get_current_admin),
    service: ProjectService = Depends(get_project_service),
):
    try:
        archived = await service.archive(project_id)
        await FastAPICache.clear(namespace="projects")
        return {
            "message": "Проект архивирован",
            "project_id": project_id,
            "title": archived.title,
        }
    except ProjectNotFoundError:
        raise HTTPException(404, "Проект не найден")
    except ProjectNotActiveError as e:
        raise HTTPException(410, str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании вопроса: {str(e)}"
        )
