class NewsServiceError(Exception):
    """Базовый класс ошибок сервиса новостей"""

    pass


class NewsNotFoundError(NewsServiceError):
    """Новость не найдена"""

    def __init__(self, message="Новость не найдена"):
        super().__init__(message)


class NewsNotActiveError(NewsServiceError):
    """Новость неактивна (архивирована или удалена)"""

    def __init__(self, message="Новость архивирована или удалена"):
        super().__init__(message)


class NothingToUpdateError(NewsServiceError):
    """Не переданы поля для обновления"""

    def __init__(self, message="Не передано ни одного поля для обновления"):
        super().__init__(message)
