from datetime import datetime

from sqlalchemy import select, desc, func

from core.send_email import send_email_notification
from db.models import Lead
from schemas.leads import LeadCreate
from services.base import BaseService
from services.leads.exceptions import (
    LeadCreationError,
    LeadNotFoundError,
    LeadNotActiveError,
    NothingToUpdateError
)


class LeadService(BaseService[Lead]):
    model = Lead
    not_found_error = LeadNotFoundError
    not_active_error = LeadNotActiveError
    nothing_to_update_error = NothingToUpdateError

    async def create_lead(self, data: LeadCreate, background_tasks) -> dict:
        """
        Создаёт заявку + планирует отправку уведомления в фоне.
        """
        try:
            lead = await self.create(
                name=data.name,
                email=data.email,
                phone=data.phone,
                subject=data.subject,
                message=data.message,
                date_created=datetime.utcnow(),
            )

            background_tasks.add_task(
                send_email_notification,
                lead_data=data
            )

            return {"detail": "Заявка успешно принята", "lead_id": lead.id}

        except Exception as e:
            await self.session.rollback()
            raise LeadCreationError(f"Ошибка сохранения заявки: {str(e)}")

    async def get_all_leads(
            self,
            skip: int = 0,
            limit: int = 100,
            active_only: bool = True,
    ) -> list[Lead]:
        """
        Получение списка всех лидов с пагинацией и
        сортировкой по дате (сначала новые)
        """
        stmt = select(self.model)

        if active_only:
            stmt = stmt.where(self.model.status == 1)

        # Сортировка по дате создания - сначала новые
        stmt = stmt.order_by(desc(self.model.date_created))

        # Пагинация
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_leads(self, active_only: bool = True) -> int:
        """
        Подсчет общего количества лидов (для пагинации)
        """
        stmt = select(func.count(self.model.id))

        if active_only:
            stmt = stmt.where(self.model.status == 1)

        return (await self.session.execute(stmt)).scalar_one()
