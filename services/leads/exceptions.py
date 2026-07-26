class LeadServiceError(Exception):
    """Базовый класс ошибок сервиса заявок"""

    pass


class LeadCreationError(LeadServiceError):
    """Ошибка при создании заявки"""

    def __init__(self, message: str = "Не удалось создать заявку"):
        super().__init__(message)

class LeadNotFoundError(Exception):
    """Лидер не найден"""
    pass

class LeadNotActiveError(Exception):
    """Лидер не активен"""
    pass

class NothingToUpdateError(Exception):
    """Нет данных для обновления"""
    pass

class LeadCreationError(Exception):
    """Ошибка создания лида"""
    pass
