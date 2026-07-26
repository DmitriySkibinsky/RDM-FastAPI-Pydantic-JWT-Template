from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from schemas.base import CamelModel


class ProjectBase(BaseModel):
    title: str = Field(..., max_length=200, description="Название проекта")
    short_description: str = Field(
        ..., max_length=500, description="Краткое описание"
    )
    full_description: str = Field(..., description="Полное описание")
    photo_url: str = Field(default="", description="URL основного изображения")
    project_url: str = Field(default="", description="URL проекта или демо")
    tags: list[str] = Field(default_factory=list, description="Теги проекта")
    client_name: str = Field(
        ..., max_length=200, description="Название клиента"
    )
    client_logo_url: str = Field(
        default="", description="URL логотипа клиента"
    )


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    short_description: str | None = Field(None, max_length=500)
    full_description: str | None = None
    photo_url: str | None = None
    project_url: str | None = None
    tags: list[str] | None = None
    client_name: str | None = Field(None, max_length=200)
    client_logo_url: str | None = None
    status: int | None = Field(None, ge=0, le=1)


class ProjectOut(CamelModel):
    id: int
    title: str
    short_description: str
    full_description: str
    photo_url: str = Field(default="")
    project_url: str = Field(default="")
    tags: list[str] = Field(default_factory=list)
    client_name: str
    client_logo_url: str = Field(default="")
    status: int
    date_created: datetime

    model_config = ConfigDict(from_attributes=True)
