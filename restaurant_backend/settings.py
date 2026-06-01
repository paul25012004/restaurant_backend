"""
Django settings — local (SQLite) ou production (Render + PostgreSQL + Cloudinary).
Variables d'environnement : voir .env.example
"""

import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- CHARGEMENT AUTOMATIQUE DU FICHIER .ENV (Local) ---
env_path = BASE_DIR / '.env'
if env_path.exists():
    import sys
    print("--- ENV DEBUG --- Loading .env file...", file=sys.stderr)
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val

# Détection robuste de Cloudinary avec toutes les variations possibles
USE_CLOUDINARY = bool(
    os.environ.get('CLOUDINARY_CLOUD_NAME') or 
    os.environ.get('CLOUDINARY_CLOUDNAME') or 
    os.environ.get('CLOUD_NAME') or 
    os.environ.get('CLOUDINARY_URL')
)


def _env_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in ('1', 'true', 'yes', 'on')


def _env_list(key: str, default: str = '') -> list[str]:
    raw = os.environ.get(key, default)
    return [x.strip() for x in raw.split(',') if x.strip()]


SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-dev-only-change-in-production',
)
DEBUG = _env_bool('DJANGO_DEBUG', True)
ALLOWED_HOSTS = _env_list('ALLOWED_HOSTS', 'localhost,127.0.0.1,*' if DEBUG else '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'core',
]

# Cloudinary — stockage média en production
if USE_CLOUDINARY:
    INSTALLED_APPS = [
        'cloudinary_storage',
        'cloudinary',
        *INSTALLED_APPS,
    ]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS local Flutter web (media servi localement)
if DEBUG and not os.environ.get('CLOUDINARY_CLOUD_NAME'):
    MIDDLEWARE.insert(2, 'core.middleware.MediaCorsMiddleware')

ROOT_URLCONF = 'restaurant_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'restaurant_backend.wsgi.application'

# --- Base de données ---
# Render : lier la base Postgres au Web Service → DATABASE_URL est injectée automatiquement.
_database_url = os.environ.get('DATABASE_URL')
_db_engine = os.environ.get('DB_ENGINE', '').lower()

if _database_url:
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.parse(
            _database_url,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
elif _db_engine in ('postgresql', 'postgres'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'chezwizi'),
            'USER': os.environ.get('DB_USER', 'chezwizi'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Abidjan'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage" if USE_CLOUDINARY else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.StaticFilesStorage",
    },
}

import sys
# Diagnostics ultra-précis pour aider l'utilisateur à identifier les erreurs de configuration sur Render
print("--- STARTUP DIAGNOSTICS: CLOUDINARY ---", file=sys.stderr)
print(f"  CLOUDINARY_CLOUD_NAME: '{os.environ.get('CLOUDINARY_CLOUD_NAME')}'", file=sys.stderr)
print(f"  CLOUDINARY_CLOUDNAME : '{os.environ.get('CLOUDINARY_CLOUDNAME')}'", file=sys.stderr)
print(f"  CLOUD_NAME           : '{os.environ.get('CLOUD_NAME')}'", file=sys.stderr)
print(f"  CLOUDINARY_URL       : '{'Configured' if os.environ.get('CLOUDINARY_URL') else 'None'}'", file=sys.stderr)
print(f"  CLOUDINARY_API_KEY   : '{'Configured' if os.environ.get('CLOUDINARY_API_KEY') or os.environ.get('API_KEY') else 'None'}'", file=sys.stderr)
print(f"  CLOUDINARY_API_SECRET: '{'Configured' if os.environ.get('CLOUDINARY_API_SECRET') or os.environ.get('API_SECRET') else 'None'}'", file=sys.stderr)
print(f"  Result -> USE_CLOUDINARY = {USE_CLOUDINARY}", file=sys.stderr)
print("---------------------------------------", file=sys.stderr)

if USE_CLOUDINARY:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    print("--- STORAGE DEBUG --- Cloudinary Storage is ACTIVE!", file=sys.stderr)
    
    # Récupération résiliente des credentials
    cloud_name = (
        os.environ.get('CLOUDINARY_CLOUD_NAME') or 
        os.environ.get('CLOUDINARY_CLOUDNAME') or 
        os.environ.get('CLOUD_NAME')
    )
    api_key = os.environ.get('CLOUDINARY_API_KEY') or os.environ.get('API_KEY')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET') or os.environ.get('API_SECRET')
    
    if cloud_name:
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': cloud_name,
            'API_KEY': api_key or '',
            'API_SECRET': api_secret or '',
        }
else:
    print("--- STORAGE DEBUG --- Cloudinary Storage is NOT active. Falling back to Local Storage.", file=sys.stderr)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User'

# CORS
_cors_origins = _env_list('CORS_ALLOWED_ORIGINS')
if _cors_origins:
    CORS_ALLOWED_ORIGINS = [origin.rstrip('/') for origin in _cors_origins]
    CORS_ALLOW_ALL_ORIGINS = False
else:
    CORS_ALLOW_ALL_ORIGINS = DEBUG

_csrf_origins = _env_list('CSRF_TRUSTED_ORIGINS')
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [origin.rstrip('/') for origin in _csrf_origins]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
