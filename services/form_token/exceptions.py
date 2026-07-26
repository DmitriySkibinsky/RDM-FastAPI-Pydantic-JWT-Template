class FormTokenError(Exception):
    """Базовое исключение для ошибок, связанных с form_token."""

class FormTokenNotFoundError(FormTokenError):
    """Токен не найден в Redis или истёк."""

class InvalidFormTokenDataError(FormTokenError):
    """Некорректные данные токена в Redis."""
