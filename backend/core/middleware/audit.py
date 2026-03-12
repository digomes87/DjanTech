import logging
import time

logger = logging.getLogger("apps.audit")


class AuditLogMiddleware:
    AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000)

        if request.method in self.AUDITED_METHODS:
            user_id = request.user.id if request.user.is_authenticated else "anonymous"
            logger.info(
                "API call",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "user_id": str(user_id),
                    "duration_ms": duration_ms,
                },
            )

        return response
