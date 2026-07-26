from sqlalchemy import select

from services.base import BaseService
from db.models import TeamMember
from services.team_members.exceptions import (
    MemberNotFoundError,
    MemberNotActiveError,
    NothingToUpdateError,
    MemberAlreadyExistsError,
)


class TeamMemberService(BaseService[TeamMember]):
    model = TeamMember
    not_found_error = MemberNotFoundError
    not_active_error = MemberNotActiveError
    nothing_to_update_error = NothingToUpdateError

    async def create(self, **kwargs) -> TeamMember:
        if "email" in kwargs and kwargs["email"]:
            stmt = (select(TeamMember)
                    .where(TeamMember.email == kwargs["email"]))

            exists = await self.session.execute(stmt)
            if exists.scalars().first():
                raise MemberAlreadyExistsError(kwargs["email"])

        return await super().create(**kwargs)
