from datetime import datetime
from typing import List, Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_serializer
)

from schemas.base import CamelModel


class TeamMemberBase(BaseModel):
    name: str = Field(..., max_length=200, description="Полное имя участника")
    job_title: str = Field(..., max_length=100, description="Должность/роль")
    experience_months: int = Field(
        default=0, ge=0, description="Опыт работы в месяцах"
    )
    photo_url: Optional[str] = Field(None, description="URL фотографии")
    email: Optional[EmailStr] = Field(None, description="Email адрес")


class TeamMemberCreate(TeamMemberBase):
    skills: Optional[List[str]] = Field(
        default_factory=list,
        description="Список навыков участника (массив строк)"
    )


class TeamMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    experience_months: Optional[int] = Field(None, ge=0)
    photo_url: Optional[str] = None
    email: Optional[str] = Field(
        None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    skills: Optional[List[str]] = Field(
        default_factory=list,
        description=("Список навыков участника (массив строк). "
                     "Передача заменяет старый список")
    )
    status: Optional[int] = Field(None, ge=0, le=1)

    model_config = ConfigDict(extra="forbid")


class TeamMemberOut(CamelModel):
    id: int
    name: str
    job_title: str
    experience_months: int
    photo_url: Optional[str] = None
    email: Optional[EmailStr] = None
    skills: List[str] = Field(default_factory=list)
    status: int
    created_at: datetime

    @field_serializer("email")
    def serialize_email(self, email: Optional[EmailStr]) -> Optional[str]:
        return str(email) if email is not None else None

    @field_serializer("skills")
    def serialize_skills(self, skills: List[str]) -> List[str]:
        return skills if skills else []
