from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from schemas.base import CamelModel


class NewsCreate(BaseModel):
    title: str = Field(
        ..., min_length=3, max_length=500, description="Заголовок новости"
    )
    text: str = Field(..., min_length=10, description="Основной текст новости")


class NewsOut(CamelModel):
    id: int
    title: str
    text: str
    status: int
    created_at: datetime


class NewsUpdate(BaseModel):
    title: str | None = Field(
        None,
        min_length=3,
        max_length=500,
        description="Новый заголовок новости (опционально)",
    )
    text: str | None = Field(
        None,
        min_length=10,
        description="Новый текст новости (опционально)",
    )

    model_config = ConfigDict(
        extra="forbid",
    )


class NewsArchiveResponse(CamelModel):
    message: str
    news_id: int
    title: str
    new_status: int = 0
