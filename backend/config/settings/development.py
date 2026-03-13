# config/settings/development.py
from .base import *  # noqa
from .base import DATABASES

DEBUG = True

# Banco local (sem Docker, direto na máquina)
DATABASES["default"]["HOST"] = "localhost"

# CORS liberado pro frontend local
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# Email imprime no terminal em vez de enviar
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
