from typing import Generic, TypeVar, Type, Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Base

M = TypeVar("M", bound=Base)


class BaseService(Generic[M]):
    model: Type[M]

    not_found_error: type[Exception]
    not_active_error: type[Exception]
    nothing_to_update_error: type[Exception]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, obj_id: int, active_only: bool = True) -> M:
        stmt = select(self.model).where(self.model.id == obj_id)
        if active_only:
            stmt = stmt.where(self.model.status == 1)

        result = await self.session.execute(stmt)
        obj = result.scalars().first()

        if not obj:
            raise self.not_found_error()

        return obj

    async def get_all_active(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None,
    ) -> list[M]:
        stmt = select(self.model).where(self.model.status == 1)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()  # type: ignore

    async def count_active(self) -> int:
        stmt = select(func.count(self.model.id)).where(self.model.status == 1)
        return (await self.session.execute(stmt)).scalar_one()

    async def create(self, **kwargs: Any) -> M:
        obj = self.model(**kwargs, status=1)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj_id: int, **kwargs: Any) -> M:
        obj = await self.get_by_id(obj_id, active_only=True)

        if not kwargs:
            raise self.nothing_to_update_error()

        for k, v in kwargs.items():
            setattr(obj, k, v)

        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def archive(self, obj_id: int) -> M:
        obj = await self.get_by_id(obj_id, active_only=False)
        if obj.status == 0:
            raise self.not_active_error("Уже архивировано")

        obj.status = 0
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
