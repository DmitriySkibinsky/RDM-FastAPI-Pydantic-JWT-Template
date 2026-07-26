from services.base import BaseService
from db.models import News
from services.news.exceptions import (
    NewsNotFoundError,
    NewsNotActiveError,
    NothingToUpdateError,
)


class NewsService(BaseService[News]):
    model = News
    not_found_error = NewsNotFoundError
    not_active_error = NewsNotActiveError
    nothing_to_update_error = NothingToUpdateError

    async def create(self, title: str, text: str) -> News:
        return await super().create(title=title.strip(), text=text.strip())
