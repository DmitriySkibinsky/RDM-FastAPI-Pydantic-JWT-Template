import logging
import secrets
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import (
    frontend,
    leads,
    login,
    news,
    projects,
    team_members,
    questions,
    form_token
)
from db.init import init_database
from core.config import settings
from services.admin.init import ensure_admin_exists

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Инициализация базы данных...")
    engine = await init_database()
    app.state.db_engine = engine

    logger.info("Проверка существования администратора...")

    async with AsyncSession(engine, expire_on_commit=False) as session:
        await ensure_admin_exists(session)
        await session.commit()

    logger.info("Подключение к Redis...")
    redis_client = aioredis.from_url(
        str(settings.redis_url),
        encoding="utf8",
        decode_responses=False,
    )
    FastAPICache.init(
        RedisBackend(redis_client),
        prefix=settings.redis_prefix
    )
    app.state.redis = redis_client

    logger.info(f"Redis подключён (prefix: {settings.redis_prefix})")
    logger.info("Приложение запущено и готово к работе")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("Закрытие подключения к БД...")
    await engine.dispose()

    logger.info("Закрытие подключения к Redis...")
    await redis_client.close()

    logger.info("Engine и Redis закрыты")

app = FastAPI(lifespan=lifespan)

SECRET_KEY = secrets.token_urlsafe(48)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="session_id",
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
)

origins = [
    
    # for dev
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "X-Requested-With",
    ],
    max_age=3600,
)

app.include_router(frontend.router, tags=["Frontend"])
app.include_router(news.router, prefix="/v1", tags=["News API v1"])
app.include_router(projects.router, prefix="/v1", tags=["Projects API v1"])
app.include_router(team_members.router, prefix="/v1", tags=["Members API v1"])
app.include_router(leads.router, prefix="/v1", tags=["Leads API v1"])
app.include_router(questions.router, prefix="/v1", tags=["Questions API v1"])
app.include_router(login.router, prefix="/v1", tags=["Auth API v1"])
app.include_router(form_token.router, prefix="/v1", tags=["Nuxt Token API v1"])
