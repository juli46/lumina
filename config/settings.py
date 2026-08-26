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
    'ckeditor',
    'ckeditor_uploader',
    'django.contrib.humanize',
    'core',
]


# =========================
# MIDDLEWARE
# =========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
        'DIRS': [BASE_DIR / 'templates'],  # 👈 IMPORTANTE
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
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
STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# =========================
# MEDIA (IMÁGENES)
# =========================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =========================
# USUARIO PERSONALIZADO
# =========================
AUTH_USER_MODEL = 'core.Usuario'


# =========================
# LOGIN / LOGOUT
# =========================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'


CKEDITOR_UPLOAD_PATH = "uploads/"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"

EMAIL_PORT = 587

EMAIL_USE_TLS = True

EMAIL_HOST_USER = "contacto.luminabeauty1@gmail.com"

EMAIL_HOST_PASSWORD = "tcbf kkrs posc obwu"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

WOMPI_PUBLIC_KEY = "pub_test_SgMYtX6qwF07LjXGOIuxUwJXlfIxpz4Y"
WOMPI_PRIVATE_KEY = "prv_test_LEFmigkPqRa8vc7MdwhmITcQwI9SiOEv"
WOMPI_ENVIRONMENT = "sandbox"
WOMPI_INTEGRITY_SECRET = "test_integrity_1yVGHZLg0vtgZGKLnrymumEkZ6DJcBf7"