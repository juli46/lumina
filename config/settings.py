import os
from pathlib import Path

# =========================
# BASE
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# SEGURIDAD
# =========================
SECRET_KEY = 'django-insecure-2ax11sm@$^t2rjkv87%#sj+8d@j%0m0x&an1j+lr34mk8l%mz0'

DEBUG = True

ALLOWED_HOSTS = []


# =========================
# APPS
# =========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # CKEditor
    'ckeditor',
    'ckeditor_uploader',

    # Lúmina
    'core',

    # Django Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django.contrib.sites',
]


# =========================
# MIDDLEWARE
# =========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Django Allauth
    'allauth.account.middleware.AccountMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]


# =========================
# URLS
# =========================
ROOT_URLCONF = 'config.urls'


# =========================
# TEMPLATES
# =========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Context processor de Lúmina
                'core.context_processors.carrito_context',
            ],
        },
    },
]


# =========================
# WSGI
# =========================
WSGI_APPLICATION = 'config.wsgi.application'


# =========================
# BASE DE DATOS
# =========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# =========================
# PASSWORD VALIDATION
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =========================
# INTERNACIONALIZACIÓN
# =========================
LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_TZ = True


# =========================
# ARCHIVOS ESTÁTICOS
# =========================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']


# =========================
# MEDIA
# =========================
MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# =========================
# USUARIO PERSONALIZADO
# =========================
AUTH_USER_MODEL = 'core.Usuario'

SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
}


# =========================
# AUTENTICACIÓN
# =========================
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]


# =========================
# LOGIN / LOGOUT
# =========================
LOGIN_URL = '/login/'

LOGIN_REDIRECT_URL = '/mi-cuenta/'

LOGOUT_REDIRECT_URL = '/'


# =========================
# DJANGO ALLAUTH
# =========================

# Permite crear automáticamente
# una cuenta de Django cuando
# alguien inicia sesión por Google
# por primera vez.
SOCIALACCOUNT_AUTO_SIGNUP = True

# Permite iniciar directamente
# el proceso OAuth al entrar
# mediante el enlace del proveedor.
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "core.adapters.LuminaSocialAccountAdapter"


# =========================
# CKEDITOR
# =========================
CKEDITOR_UPLOAD_PATH = 'uploads/'


# =========================
# EMAIL
# =========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 587

EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'contacto.luminabeauty1@gmail.com'

EMAIL_HOST_PASSWORD = 'tcbf kkrs posc obwu'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# =========================
# WOMPI
# =========================
WOMPI_PUBLIC_KEY = 'pub_test_SgMYtX6qwF07LjXGOIuxUwJXlfIxpz4Y'

WOMPI_PRIVATE_KEY = 'prv_test_LEFmigkPqRa8vc7MdwhmITcQwI9SiOEv'

WOMPI_ENVIRONMENT = 'sandbox'

WOMPI_INTEGRITY_SECRET = 'test_integrity_1yVGHZLg0vtgZGKLnrymumEkZ6DJcBf7'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "allauth": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

# =========================
# SEGURIDAD
# =========================
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'clave-local-solo-para-desarrollo'
)

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1'
).split(',')

RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = []

if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(
        f'https://{RENDER_EXTERNAL_HOSTNAME}'
    )