from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from api.utils.key_builder import query_aware_key_builder
from core.dependencies import get_current_admin
from db.models import TeamMember
from db.session import get_db_session
from services.team_members.service import TeamMemberService
from schemas.team_members import (
    TeamMemberCreate,
    TeamMemberOut,
    TeamMemberUpdate
)
from services.team_members.exceptions import (
    MemberAlreadyExistsError,
    MemberNotActiveError,
    MemberNotFoundError,
    NothingToUpdateError,
)


router = APIRouter(prefix="/team-members")


def get_team_member_service(
    session=Depends(get_db_session),
) -> TeamMemberService:
    return TeamMemberService(session)


@router.get(
    "",
    response_model=list[TeamMemberOut],
    summary="Список всех активных членов команды",
    description= (
            "Возвращает список всех участников команды "
            "со статусом 'активен' (status=1)"),
    responses={
        200: {"description": "Список активных участников команды"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
@cache(expire=300,
       namespace="team-members:list",
       key_builder=query_aware_key_builder
)
async def get_active_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: TeamMemberService = Depends(get_team_member_service),
):
    members = await service.get_all_active(
        skip=skip, limit=limit, order_by=TeamMember.created_at.desc()
    )
    return [TeamMemberOut.model_validate(m) for m in members]


@router.get(
    "/{member_id}",
    response_model=TeamMemberOut,
    summary="Получить информацию об участнике",
    description="Возвращает полную информацию об участнике команды по его ID",
    responses={
        200: {"description": "Информация об участнике"},
        404: {"description": "Участник не найден"},
        410: {"description": "Участник неактивен"},
        500: {"description": "Внутренняя ошибка сервера"},
    },
)
@cache(expire=180,
       namespace="team-members:detail",
       key_builder=query_aware_key_builder
)
async def get_team_member(
    member_id: int,
    service: TeamMemberService = Depends(get_team_member_service),
):
    try:
        member = await service.get_by_id(member_id)
        return TeamMemberOut.model_validate(member)
    except MemberNotFoundError:
        raise HTTPException(404, "Участник не найден")
    except MemberNotActiveError:
        raise HTTPException(410, "Участник неактивен")


@router.post(
    "",
    response_model=TeamMemberOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового участника команды",
    description=(
        "Создаёт нового участника команды.\n\n"
        "**Доступ:** только администраторы\n"
        "Навыки передаются в поле skills как массив строк."
    ),
    responses={
        201: {"description": "Участник успешно создан"},
        400: {"description": "Участник с таким email уже существует"},
        401: {"description": "Требуется авторизация администратора"},
        422: {"description": "Ошибка валидации данных"},
        500: {"description": "Ошибка создания участника"},
    },
)
async def create_member(
        data: TeamMemberCreate,
        _admin=Depends(get_current_admin),
        service: TeamMemberService = Depends(get_team_member_service),
):
    try:
        member = await service.create(**data.model_dump())
        await FastAPICache.clear(namespace="team-members")
        return TeamMemberOut.model_validate(member)

    except MemberAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except MemberNotFoundError:
        raise HTTPException(404, "Участник не найден")
    except MemberNotActiveError:
        raise HTTPException(410, "Нельзя работать с неактивным участником")
    except Exception as e:
        raise HTTPException(500, f"Внутренняя ошибка: {str(e)}")


@router.put(
    "/{member_id}",
    response_model=TeamMemberOut,
    summary="Обновление информации об участнике",
    description=(
        "Частичное обновление данных участника.\n"
        "Обновляются только переданные поля.\n"
        "**Доступ:** только администраторы\n"
        "Навыки полностью заменяются при передаче поля skills (массив строк)."
    ),
    responses={
        200: {"description": "Участник успешно обновлён"},
        400: {"description": "Не переданы поля для обновления"},
        401: {"description": "Требуется авторизация администратора"},
        404: {"description": "Участник не найден"},
        410: {"description": "Нельзя редактировать неактивного участника"},
        422: {"description": "Ошибка валидации данных"},
        500: {"description": "Ошибка обновления участника"},
    },
)
async def update_team_member(
    member_id: int,
    data: TeamMemberUpdate,
    _admin=Depends(get_current_admin),
    service: TeamMemberService = Depends(get_team_member_service),
):
    update_dict = data.model_dump(exclude_unset=True)
    skills = update_dict.pop("skills", None)

    try:
        member = await service.update(member_id, **update_dict)

        if skills is not None:
            member.skills = skills if skills else []
            await service.session.commit()
            await service.session.refresh(member)

        await FastAPICache.clear(namespace="team-members")
        return TeamMemberOut.model_validate(member)
    except MemberNotFoundError:
        raise HTTPException(404, "Участник не найден")
    except MemberNotActiveError:
        raise HTTPException(410, "Нельзя редактировать неактивного участника")
    except NothingToUpdateError:
        raise HTTPException(400, "Не передано ни одного поля для обновления")


@router.delete(
    "/{member_id}",
    summary="Удаление (архивирование) участника",
    description=(
        "Выполняет мягкое удаление участника — устанавливает status=0.\n\n"
        "**Доступ:** только администраторы\n"
        "Участник остаётся в базе, его можно восстановить."
    ),
    responses={
        200: {"description": "Участник успешно архивирован"},
        401: {"description": "Требуется авторизация администратора"},
        404: {"description": "Участник не найден"},
        410: {"description": "Участник уже удалён"},
        500: {"description": "Ошибка удаления участника"},
    },
)
async def archive_member(
    member_id: int,
    _admin=Depends(get_current_admin),
    service: TeamMemberService = Depends(get_team_member_service),
):
    try:
        archived = await service.archive(member_id)
        await FastAPICache.clear(namespace="team-members")
        return {
            "message": "Участник архивирован",
            "member_id": member_id,
            "name": archived.name,
            "job_title": archived.job_title,
        }
    except MemberNotFoundError:
        raise HTTPException(404, "Участник не найден")
    except MemberNotActiveError as e:
        raise HTTPException(410, str(e))
