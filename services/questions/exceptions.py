class QuestionServiceError(Exception):
    """Базовый класс для всех ошибок сервиса вопросов"""

    pass


class QuestionNotFoundError(QuestionServiceError):
    """Вопрос с указанным ID не найден"""

    def __init__(self, message="Вопрос не найден"):
        super().__init__(message)


class QuestionAlreadyExistsError(QuestionServiceError):
    """Вопрос с таким заголовком уже существует"""

    def __init__(self, title: str):
        super().__init__(f"Вопрос с заголовком '{title}' уже существует")


class QuestionNotActiveError(QuestionServiceError):
    """Вопрос архивирован или находится в неактивном статусе"""

    def __init__(self, message="Вопрос не активен"):
        super().__init__(message)


class NothingToUpdateError(QuestionServiceError):
    """Не переданы поля для обновления (все поля None или не указаны)"""

    def __init__(self, message="Не передано ни одного поля для обновления"):
        super().__init__(message)
