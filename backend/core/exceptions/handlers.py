"""
Custom exceptions and global exception handler.
Define your own exception hierarchy so views can catch specific
business errors and return appropriate HTTP codes.
"""

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


# ── Domain exceptions ─────────────────────────────────────────────────────────


class FintechBaseException(Exception):
    default_message = "An error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class BusinessRuleViolation(FintechBaseException):
    default_message = "Business rule violation."


class InvalidStatusTransition(FintechBaseException):
    default_message = "Invalid status transition."


class InsufficientPermissions(FintechBaseException):
    default_message = "You don't have permission to perform this action."


class ExternalServiceError(FintechBaseException):
    default_message = "External service unavailable."


# ── Global exception handler ──────────────────────────────────────────────────


def custom_exception_handler(exc, context):
    """
    Extends DRF's default handler:
    1. Handles our custom domain exceptions
    2. Adds consistent error envelope: {"detail": "...", "code": "...", "status": N}
    3. Logs 5xx errors
    """
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "detail": response.data.get("detail", str(exc)),
            "code": getattr(exc, "default_code", "error"),
            "status": response.status_code,
        }
        return response

    if isinstance(exc, (BusinessRuleViolation, InvalidStatusTransition)):
        logger.warning(f"Domain error: {exc}")
        return Response(
            {"detail": str(exc), "code": "business_rule_violation", "status": 422},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if isinstance(exc, InsufficientPermissions):
        return Response(
            {"detail": str(exc), "code": "insufficient_permissions", "status": 403},
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, ExternalServiceError):
        logger.error(f"External service error: {exc}", exc_info=True)
        return Response(
            {
                "detail": "External service temporarily unavailable. Please try again.",
                "status": 503,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return Response(
        {"detail": "An unexpected error occurred.", "status": 500},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
