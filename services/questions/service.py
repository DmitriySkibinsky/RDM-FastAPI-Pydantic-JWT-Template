from sqlalchemy import select

from services.base import BaseService
from db.models import Question
from schemas.questions import QuestionCreate
from services.questions.exceptions import (
    QuestionNotFoundError,
    QuestionNotActiveError,
    NothingToUpdateError,
    QuestionAlreadyExistsError,
)


class QuestionService(BaseService[Question]):
    model = Question
    not_found_error = QuestionNotFoundError
    not_active_error = QuestionNotActiveError
    nothing_to_update_error = NothingToUpdateError

    async def create_question(self, data: QuestionCreate) -> Question:
        exists = await self.session.execute(
            select(Question).where(Question.title == data.title)
        )
        if exists.scalars().first():
            raise QuestionAlreadyExistsError(data.title)

        return await self.create(**data.model_dump())
