from django.db import connection
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({"status": "ok" if db_ok else "degraded", "db": db_ok})


urlpatterns = [path("", health_check, name="health_check")]
