from __future__ import annotations


class AppError(Exception):
    """Base class for controlled application errors."""


class AuthenticationError(AppError):
    pass


class AuthorizationError(AppError):
    pass


class ValidationError(AppError):
    pass


class RateLimitError(AppError):
    pass


class IntegrityError(AppError):
    pass
