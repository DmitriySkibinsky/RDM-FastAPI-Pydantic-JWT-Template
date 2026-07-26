from pydantic import BaseModel, Field

from schemas.base import CamelModel


class QuestionBase(BaseModel):
    title: str = Field(...,
                       max_length=500,
                       description="Заголовок вопроса")
    answer: str = Field(...,
                        description="Ответ на вопрос (может быть многострочным)")


class QuestionCreate(QuestionBase):
    """Схема для создания нового вопроса (FAQ)"""
    pass


class QuestionUpdate(BaseModel):
    """Схема для частичного обновления вопроса"""
    title: str | None = Field(None, max_length=500)
    answer: str | None = None
    status: int | None = Field(None, ge=0, le=1)


class QuestionOut(CamelModel):
    """Схема ответа — полный объект вопроса"""
    id: int
    title: str
    answer: str
    status: int = Field(..., ge=0, le=1)
