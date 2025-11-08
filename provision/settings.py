import os
import logging
import json
from pathlib import Path
from urllib.parse import urlparse
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

logger = logging.getLogger(__name__)
# =====================================================================
# 1. CONFIGURAÇÕES BÁSICAS E DE AMBIENTE
# =====================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Detecção e Variáveis Críticas ---
IS_CLOUD_RUN_PRODUCTION = os.getenv("IS_CLOUD_RUN") == "True" or os.getenv("K_SERVICE") is not None

# Secrets e Debug
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-development")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1" and not IS_CLOUD_RUN_PRODUCTION

# Hosts permitidos
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,*.run.app").split(",")
    if h.strip()
]

# 2. Adicionar o domínio personalizado
ALLOWED_HOSTS.append("*.crcttec.com.br")
ALLOWED_HOSTS.append("www.crcttec.com.br")
ALLOWED_HOSTS.append(".run.app")

from django.core.management.utils import get_random_secret_key 
try:
    from django.conf import settings
    # Captura o host dinâmico se a aplicação estiver rodando
    if 'HTTP_HOST' in os.environ:
        host_header = os.environ['HTTP_HOST']
        if host_header not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host_header)
except Exception:
    pass

# Opcional: Adiciona o domínio interno do Cloud Run para saúde e comunicação interna
if IS_CLOUD_RUN_PRODUCTION and os.getenv('K_SERVICE'):
    ALLOWED_HOSTS.append(f"{os.getenv('K_SERVICE')}-{os.getenv('K_REVISION')}.{os.getenv('K_SERVICE')}.svc.cluster.local")


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
    "pytest_django",

    # Third party
    "rest_framework",
    "drf_spectacular",
    "oauth2_provider",

    # Google Cloud Storage
    'storages', 

    # Django Crispy Forms
    "crispy_forms",
    "crispy_bootstrap5",

    # Aplicativos Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

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
    'allauth.account.middleware.AccountMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "provision.urls"
WSGI_APPLICATION = "provision.wsgi.application"

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

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =====================================================================
# 2. CONFIGURAÇÃO DE BANCOS DE DADOS E PERSISTÊNCIA
# =====================================================================

# --- Variáveis de Conexão (Unificadas para o Workflow YAML) ---
DB_ENGINE = os.getenv("DJANGO_DB_ENGINE", "django.db.backends.mysql")
DB_NAME = os.getenv("DB_NAME", "provision_db")
DB_USER = os.getenv("DB_USER", "provision_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")

# --- MySQL (Cloud SQL / Local) ---
if IS_CLOUD_RUN_PRODUCTION and CLOUD_SQL_CONNECTION_NAME:
    # Perfil de Produção: Conexão Cloud SQL via Unix Socket
    logger.error(f"DEBUG: Tentando conectar ao socket UNIX em: /cloudsql/{CLOUD_SQL_CONNECTION_NAME}")
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE, 
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": 'localhost',
            "OPTIONS": {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                # Conexão via socket Unix do Cloud SQL Proxy
                "unix_socket": f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}", 
            }
        }
    }
    # Otimização: manter conexões ativas no ambiente serverless
    DATABASES["default"]["CONN_MAX_AGE"] = int(os.getenv("DJANGO_CONN_MAX_AGE", 60))

else:
    # Perfil de Desenvolvimento Local / MySQL Local
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE, 
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
            "OPTIONS": {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# --- MongoDB (Atlas) - RESTAURADO ---
MONGODB_URI = os.getenv("MONGODB_URI") 
MONGODB = {}

if MONGODB_URI:
    # Conexão via URI completa (padrão para MongoDB Atlas)
    parsed_uri = urlparse(MONGODB_URI)
    
    MONGODB = {
        "URI": MONGODB_URI,
        "HOST": parsed_uri.hostname,
        "PORT": parsed_uri.port or 27017,
        "DB_NAME": os.getenv("MONGODB_DB_NAME", parsed_uri.path.strip('/') or "provision_mongo"),
        "USER": parsed_uri.username,
        "PASSWORD": parsed_uri.password,
    }
else:
    # Fallback para Localhost
    MONGODB = {
        "HOST": os.getenv("MONGODB_HOST", "localhost"),
        "PORT": int(os.getenv("MONGODB_PORT", 27017)),
        "DB_NAME": os.getenv("MONGODB_DB_NAME", "provision_mongo"),
        "USER": os.getenv("MONGODB_USER", ""),
        "PASSWORD": os.getenv("MONGODB_PASSWORD", ""),
    }


# --- Arquivos Estáticos e de Mídia (GCS) ---

# Usa a detecção robusta de ambiente
if IS_CLOUD_RUN_PRODUCTION and os.getenv("GS_BUCKET_NAME"):
    
    GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
     
    # 1. Ativa a assinatura de URL (exige credenciais com chave privada)
    GS_QUERYSTRING_AUTH = True 
    
    # 2. Carrega as credenciais injetadas do Secret Manager (Cloud Run injeta o JSON direto)
    # O nome da variável de ambiente no Cloud Run DEVE ser GCS_SA_KEY_B64
    GCS_SA_KEY_JSON = os.getenv("GCS_SA_KEY_B64")
    GS_CREDENTIALS = None
    
    if GCS_SA_KEY_JSON:
        logger.info("Credencial GCS (JSON) encontrada. Tentando carregar...")
        try:
            GCS_SA_KEY_DICT = json.loads(GCS_SA_KEY_JSON)
            GS_CREDENTIALS = ServiceAccountCredentials.from_service_account_info(GCS_SA_KEY_DICT)
            logger.info("Chave GCS carregada com sucesso do Secret.")
        except json.JSONDecodeError as e:
            # Mantemos o log de erro caso o Secret Manager injete algo inválido
            logger.error(f"Erro CRÍTICO ao decodificar JSON da chave GCS: {e}")
            logger.error(f"Valor JSON (Primeiros 100 caracteres): {GCS_SA_KEY_JSON[:100]}...")
    
    # ----------------------------------------------------
    
    # Define os backends de armazenamento para Django 4.2+
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": GS_BUCKET_NAME,
                # 3. Injeta a chave JSON decodificada
                "credentials": GS_CREDENTIALS, 
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": GS_BUCKET_NAME,
                "credentials": GS_CREDENTIALS,
            },
        },
    }
    
    # As URLs continuam apontando para o GCS
    STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"
    STATICFILES_DIRS = [BASE_DIR / "static"] 
    STATIC_ROOT = BASE_DIR / "staticfiles_collected" 
    
else:
    # Desenvolvimento Local/Build do Docker: Uso do sistema de arquivos local
    STATIC_URL = "/static/"
    STATIC_ROOT = BASE_DIR / "staticfiles"
    STATICFILES_DIRS = [BASE_DIR / "static"]

TEST_RUNNER = 'pytest_django.runner.TestRunner'

# =====================================================================
# 3. AUTENTICAÇÃO, API E SEGURANÇA
# =====================================================================

# --- Autenticação e Allauth ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL", "/")
ACCOUNT_LOGOUT_REDIRECT_URL = os.getenv("ACCOUNT_LOGOUT_REDIRECT_URL", "/")
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_ALLOW_REGISTRATION = True
ACCOUNT_SIGNUP_PASSWORD_RETYPE = True
ACCOUNT_EMAIL_VERIFICATION = os.getenv("ACCOUNT_EMAIL_VERIFICATION", "mandatory")
LOGIN_URL = '/account/login/' 
ACCOUNT_LOGOUT_REDIRECT_URL = '/account/login/'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
    },
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
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
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


# --- Configurações de Segurança e Cloud Run ---
if not DEBUG and IS_CLOUD_RUN_PRODUCTION:
    # Cloud Run usa HTTPS, forçamos cookies seguros
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS ativado
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000")) 
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Configuração crucial: Cloud Run/Load Balancer enviam este cabeçalho
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

else:
    # Configurações de segurança para ambiente local
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
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}

EMAIL_BACKEND = os.getenv("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT") or 25)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "webmaster@localhost")