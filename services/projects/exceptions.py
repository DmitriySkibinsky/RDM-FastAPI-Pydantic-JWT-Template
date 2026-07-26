class ProjectServiceError(Exception):
    """Базовый класс для всех ошибок сервиса проектов"""

    pass


class ProjectNotFoundError(ProjectServiceError):
    """Проект с указанным ID не найден"""

    def __init__(self, message="Проект не найден"):
        super().__init__(message)


class ProjectAlreadyExistsError(ProjectServiceError):
    """Проект с таким названием уже существует"""

    def __init__(self, title: str):
        super().__init__(f"Проект с названием '{title}' уже существует")


class ProjectNotActiveError(ProjectServiceError):
    """Проект архивирован, удалён или находится в неактивном статусе"""

    def __init__(self, message="Проект не активен"):
        super().__init__(message)


class NothingToUpdateError(ProjectServiceError):
    """Не переданы поля для обновления (все поля None или не указаны)"""

    def __init__(self, message="Не передано ни одного поля для обновления"):
        super().__init__(message)
