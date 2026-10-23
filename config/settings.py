import os
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DEBUG") == "1"
BUILD_STATIC = os.environ.get("BUILD_STATIC") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if DEBUG or BUILD_STATIC:
    SECRET_KEY = SECRET_KEY or "local-development-only-never-use-in-production"
if len(SECRET_KEY) < 40:
    raise ImproperlyConfigured("Set SECRET_KEY to at least 40 random characters.")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG or BUILD_STATIC else "").split(",")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:18001" if DEBUG or BUILD_STATIC else "").rstrip("/")
if not DEBUG and not BUILD_STATIC and (not ALLOWED_HOSTS[0] or urlparse(PUBLIC_URL).scheme != "https"):
    raise ImproperlyConfigured("Production requires ALLOWED_HOSTS and an HTTPS PUBLIC_URL.")
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.staticfiles", "study"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "study.middleware.LanguageMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request", "study.i18n.context"]}}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ.get("DATABASE_PATH", BASE_DIR / "data/db.sqlite3"), "OPTIONS": {"timeout": 10}}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Pacific/Auckland"
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_AGE = 60 * 60 * 12
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = [PUBLIC_URL] if PUBLIC_URL else []
# The reverse proxy must overwrite X-Forwarded-Proto and isolate this service.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG and not BUILD_STATIC
SECURE_HSTS_SECONDS = 31536000 if not DEBUG and not BUILD_STATIC else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
LESSON_DIR = BASE_DIR / "lessons"
