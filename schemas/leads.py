from datetime import datetime
from typing import Self, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    model_validator
)


class LeadCreate(BaseModel):
    """Схема для создания новой заявки"""

    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr | None = Field(default=None)
    phone: str | None = Field(default=None, min_length=5, max_length=50)
    subject: str = Field(..., min_length=2, max_length=255)
    message: str = Field(..., min_length=10)

    token: str = Field(...,
                       min_length=8,
                       description="Токен формы")

    @model_validator(mode="before")
    @classmethod
    def empty_strings_to_none(cls, data: dict | object) -> dict | object:
        if not isinstance(data, dict):
            return data

        for field in ("email", "phone"):
            if field in data and data[field] == "":
                data[field] = None

        return data

    @model_validator(mode="after")
    def require_at_least_one_contact(self) -> Self:
        if self.email is None and self.phone is None:
            raise ValueError("Необходимо указать хотя бы одно из полей: email или phone")

        return self
    @classmethod
    def model_validate_debug(cls, obj):
        """Метод для отладки валидации"""
        print("\n" + "=" * 50)
        print("DEBUG model_validate:")
        if isinstance(obj, dict):
            for k, v in obj.items():
                print(f"  {k}: type={type(v)}, value={repr(v)}")
        return cls.model_validate(obj)

class LeadEmailData(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    subject: str
    message: str


class LeadResponse(BaseModel):
    """Схема для ответа с данными лида"""
    id: int
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    subject: str
    message: str
    date_created: datetime
    status: int

    class Config:
        from_attributes = True


class LeadsListResponse(BaseModel):
    """Схема для ответа со списком лидов и мета-информацией"""
    items: list[LeadResponse]
    total: int
    skip: int
    limit: int
