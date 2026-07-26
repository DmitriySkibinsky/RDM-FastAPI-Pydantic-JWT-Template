from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    SmallInteger,
    Text,
    inspect,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY, JSONB


class Base(DeclarativeBase):
    def to_dict(self) -> dict[str, Any]:
        """
        Универсальный метод для преобразования модели в словарь.
        """
        data = {}
        for column in inspect(self).mapper.column_attrs:
            key = column.key
            value = getattr(self, key)

            if isinstance(value, datetime):
                value = value.isoformat()

            data[key] = value

        return data


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        index=True,
    )


class TeamMember(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    job_title: Mapped[str] = mapped_column(Text, nullable=False)
    experience_months: Mapped[int] = mapped_column(default=0)
    photo_url: Mapped[str] = mapped_column(Text, nullable=True)
    email: Mapped[str] = mapped_column(Text, nullable=True)
    skills: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="[]",
        comment="Список навыков в формате JSON массива строк"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    project_url: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    tags: Mapped[list[str]] = mapped_column(
        PG_ARRAY(Text), nullable=False, server_default="{}"
    )
    client_name: Mapped[str] = mapped_column(Text, nullable=False)
    client_logo_url: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=""
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )

    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(Text, nullable=True)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    date_created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1"
    )
