class TeamMemberServiceError(Exception):
    """Базовый класс ошибок сервиса участников команды"""

    pass


class MemberNotFoundError(TeamMemberServiceError):
    """Участник команды не найден"""

    def __init__(self, message="Участник не найден"):
        super().__init__(message)


class MemberNotActiveError(TeamMemberServiceError):
    """Участник неактивен (архивирован)"""

    def __init__(self, message="Участник неактивен"):
        super().__init__(message)


class MemberAlreadyExistsError(TeamMemberServiceError):
    """Участник с таким email уже существует"""

    def __init__(self, email: str):
        super().__init__(f"Участник с email '{email}' уже существует")


class NothingToUpdateError(TeamMemberServiceError):
    """Не переданы данные для обновления"""

    def __init__(self, message="Не передано ни одного поля для обновления"):
        super().__init__(message)


class InvalidSkillIdError(TeamMemberServiceError):
    """Один или несколько указанных ID навыков не существуют"""

    pass
