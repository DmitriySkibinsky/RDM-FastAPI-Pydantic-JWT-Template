from pydantic import BaseModel, Field


class FormTokenCreate(BaseModel):
    form_token: str = Field(...,
                            min_length=8,
                            description="Токен формы")
    nuxt_auth_token: str = Field(...,
                            description="Секрет Nuxt для авторизации запроса")
