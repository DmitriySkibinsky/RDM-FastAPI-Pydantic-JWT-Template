from datetime import datetime
from sqlalchemy import select

from services.base import BaseService
from db.models import Project
from services.projects.exceptions import (
    ProjectNotFoundError,
    ProjectNotActiveError,
    NothingToUpdateError,
    ProjectAlreadyExistsError,
)


class ProjectService(BaseService[Project]):
    model = Project
    not_found_error = ProjectNotFoundError
    not_active_error = ProjectNotActiveError
    nothing_to_update_error = NothingToUpdateError

    async def create(self, **kwargs) -> Project:
        if "title" in kwargs:
            exists = await self.session.execute(
                select(Project).where(Project.title == kwargs["title"])
            )
            if exists.scalars().first():
                raise ProjectAlreadyExistsError(kwargs["title"])
        return await super().create(**kwargs, date_created=datetime.now())
