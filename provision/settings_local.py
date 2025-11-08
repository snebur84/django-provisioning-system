import os
from pathlib import Path
from urllib.parse import urlparse

# Load .env (optional but recommended). If python-dotenv is not installed, this silently
# does nothing and environment variables will be read from the process environment.
try:
    from dotenv import load_dotenv

    BASE_DIR = Path(__file__).resolve().parent.parent
    dotenv_path = BASE_DIR / ".env"
    load_dotenv(dotenv_path=str(dotenv_path))
except Exception:
    BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================================
# 1. CONFIGURAÇÕES BÁSICAS E DE AMBIENTE (LOCAL)
# =====================================================================

SECRET_KEY = "5YgAhHqOkwaTB0Suhk_hzgSUe_uDbehtLkiDJEsTkuwttvA_cLJ7x0OytG4ayeEyw74"
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,192.168.0.16").split(",")
    if h.strip()
]

# --- Definição de Aplicação ---
INSTALLED_APPS = [
    # Default Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Third party
    "rest_framework",
    "drf_spectacular",
    "oauth2_provider",

    # Django Crispy Forms
    "crispy_forms",
    "crispy_bootstrap5",

    # Allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # Local apps
    "core",
    "api",
]

SITE_ID = 1

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "provision.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "provision.wsgi.application"

# =====================================================================
# 2. CONFIGURAÇÃO DE BANCOS DE DADOS E PERSISTÊNCIA (LOCAL - SQLITE)
# =====================================================================

# Use SQLite for local development. You can override the path with SQLITE_PATH in .env
SQLITE_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "db.sqlite3"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SQLITE_PATH,
    }
}

# Keep CONN_MAX_AGE in case some components depend on it (no effect for sqlite but safe)
DATABASES["default"]["CONN_MAX_AGE"] = int(os.getenv("DJANGO_CONN_MAX_AGE", 0))

# === MongoDB (Atlas via full URI) ===
# Provide MONGODB_URI in the .env (recommended) e.g.:
# MONGODB_URI=mongodb+srv://user:password@cluster0.xxxxxx.mongodb.net/provision_mongo?retryWrites=true&w=majority
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()

if MONGODB_URI:
    parsed_uri = urlparse(MONGODB_URI)
    MONGODB = {
        "URI": MONGODB_URI,
        "HOST": parsed_uri.hostname,
        "PORT": parsed_uri.port or 27017,
        # Nome do DB pode vir da URI path (ex: /provision_mongo) ou do env MONGODB_DB_NAME
        "DB_NAME": os.getenv("MONGODB_DB_NAME", parsed_uri.path.strip("/") or "provision_mongo"),
        "USER": parsed_uri.username,
        "PASSWORD": parsed_uri.password,
    }
else:
    # Fallback para desenvolvimento local sem Atlas
    MONGODB = {
        "HOST": os.getenv("MONGODB_HOST", "localhost"),
        "PORT": int(os.getenv("MONGODB_PORT", 27017)),
        "DB_NAME": os.getenv("MONGODB_DB_NAME", "provision_mongo"),
        "USER": os.getenv("MONGODB_USER", ""),
        "PASSWORD": os.getenv("MONGODB_PASSWORD", ""),
    }

# em settings.py, seção de static (dev)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # já existe

TEST_RUNNER = 'pytest_django.runner.TestRunner'
# Adicione as pastas onde seus arquivos estáticos estão atualmente

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================================================
# 3. AUTENTICAÇÃO, API E SEGURANÇA
# =====================================================================

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL", "/")
ACCOUNT_LOGOUT_REDIRECT_URL = os.getenv("ACCOUNT_LOGOUT_REDIRECT_URL", "/")
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_ALLOW_REGISTRATION = True
ACCOUNT_SIGNUP_PASSWORD_RETYPE = True
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
LOGIN_URL = "/account/login/"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- REST Framework e OAuth2 ---
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Provision API",
    "DESCRIPTION": "API de Provisionamento - documentação OpenAPI gerada pelo drf-spectacular.",
    "VERSION": "1.0.0",
    "COMPONENTS": {
        "securitySchemes": {
            "oauth2": {
                "type": "oauth2",
                "flows": {
                    "clientCredentials": {
                        "tokenUrl": "/o/token/",
                        "scopes": {
                            "read": "Read scope",
                            "write": "Write scope",
                            "provision": "Access device provisioning endpoints",
                            "admin": "Admin-level access",
                        },
                    }
                },
            }
        }
    },
    "SECURITY": [{"oauth2": ["provision", "read"]}],
}

OAUTH2_PROVIDER = {
    "ACCESS_TOKEN_EXPIRE_SECONDS": int(os.getenv("OAUTH_ACCESS_TOKEN_EXPIRE", 3600)),
    "REFRESH_TOKEN_EXPIRE_SECONDS": int(os.getenv("OAUTH_REFRESH_TOKEN_EXPIRE", 60 * 60 * 24 * 30)),
    "ROTATE_REFRESH_TOKEN": True,
    "SCOPES": {
        "read": "Read scope",
        "write": "Write scope",
        "provision": "Access device provisioning endpoints",
        "admin": "Admin-level access",
    },
}

PROVISION_API_KEY = os.getenv("PROVISION_API_KEY", "")

# --- Segurança mínima para LOCAL (não force HTTPS) ---
# Em ambiente local usamos flags definidas por variáveis de ambiente; não há lógica específica de Cloud Run.
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "0") == "1"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "0") == "1"
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "0") == "1"

# --- Logging e Email ---
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "standard"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

EMAIL_BACKEND = os.getenv("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT") or 25)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "0") == "1"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")