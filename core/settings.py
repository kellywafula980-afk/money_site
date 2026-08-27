"""
Django settings for core project.
"""
import os
import dj_database_url
from pathlib import Path

# ========== LOAD ENVIRONMENT VARIABLES ==========
# Load .env file for local development
from dotenv import load_dotenv
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ========== SECURITY WARNING ==========
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-key-change-in-production!')

# Hosts allowed to serve the application
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'globalgigs-0096.onrender.com,127.0.0.1,localhost'
).split(',')

# ========== APPLICATION DEFINITION ==========
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Your custom apps
    'jobs',
    'dashboard',
    'django.contrib.sitemaps',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'

# ========== DUAL DATABASE CONFIGURATION ==========
# Render PostgreSQL (Default DB)
RENDER_DB_URL = os.environ.get('DATABASE_URL')

# Supabase PostgreSQL (Secondary DB)
SUPABASE_DB_URL = os.environ.get('SUPABASE_DATABASE_URL')

DATABASES = {
    # Primary / Render Database
    'default': dj_database_url.config(
        default=RENDER_DB_URL,
        conn_max_age=600,
        ssl_require=True
    ) if RENDER_DB_URL else {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },

    # Supabase Database
    'supabase': dj_database_url.config(
        default=SUPABASE_DB_URL,
        conn_max_age=600,
        ssl_require=True
    ) if SUPABASE_DB_URL else {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_supabase.sqlite3',
    }
}

# UTF-8 client encoding fix for all PostgreSQL connections
for db_key in DATABASES:
    if 'postgresql' in DATABASES[db_key].get('ENGINE', ''):
        DATABASES[db_key].setdefault('OPTIONS', {})['options'] = '-c client_encoding=utf8'

# Enable Multi-Database Router
DATABASE_ROUTERS = ['core.db_router.DualDatabaseRouter']

# ========== PASSWORD VALIDATION ==========
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========== INTERNATIONALIZATION ==========
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ========== STATIC FILES (CSS, JavaScript, Images) ==========
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ========== MEDIA FILES ==========
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ========== PAYSTACK CONFIGURATION ==========
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_dummy_key')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_dummy_key')

PAYSTACK_CALLBACK_URL = os.environ.get(
    'PAYSTACK_CALLBACK_URL',
    'https://globalgigs-0096.onrender.com/payment/callback/'
)

if not DEBUG and (PAYSTACK_PUBLIC_KEY == 'pk_test_dummy_key' or PAYSTACK_SECRET_KEY == 'sk_test_dummy_key'):
    raise ValueError("Paystack keys (PUBLIC & SECRET) must be set in production environment!")

# ========== AUTHENTICATION SETTINGS ==========
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'home'

# ========== DEFAULT AUTO FIELD ==========
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========== PRODUCTION SECURITY HEADERS ==========
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'