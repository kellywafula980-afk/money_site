"""
Django settings for core project.
"""
import os
import dj_database_url
from pathlib import Path

# ========== LOAD ENVIRONMENT VARIABLES ==========
# Load .env file for local development (does nothing on Render)
from dotenv import load_dotenv
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ========== SECURITY WARNING ==========
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Secret Key with fallback for local development
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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For serving static files efficiently
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

# ========== DATABASE CONFIGURATION ==========
# Render provides DATABASE_URL for PostgreSQL.
# If not present, fallback to SQLite (local development or Render fallback).
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Use PostgreSQL (production on Render, or external DB)
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
    # Force UTF-8 client encoding to prevent UnicodeDecodeError crashes
    DATABASES['default']['OPTIONS'] = {
        'options': '-c client_encoding=utf8'
    }
else:
    # Fallback to SQLite
    IS_RENDER = 'RENDER' in os.environ
    if IS_RENDER:
        # Render's ephemeral disk - use /opt/render/project/src/data
        RENDER_DATA_DIR = '/opt/render/project/src/data'
        if not os.path.exists(RENDER_DATA_DIR):
            os.makedirs(RENDER_DATA_DIR)
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(RENDER_DATA_DIR, 'db.sqlite3'),
            }
        }
    else:
        # Local development SQLite
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

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

# Use WhiteNoise storage (compressed manifest in production, standard in dev)
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ========== MEDIA FILES (Uploaded Resumes, etc.) ==========
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ========== PAYSTACK PAYMENT CONFIGURATION ==========
PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_dummy_key')
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_dummy_key')

PAYSTACK_CALLBACK_URL = os.environ.get(
    'PAYSTACK_CALLBACK_URL',
    'https://globalgigs-0096.onrender.com/payment/callback/'
)

# Raise an error if Paystack keys are missing when DEBUG=False (Production)
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
    # Redirect all HTTP traffic to HTTPS
    SECURE_SSL_REDIRECT = True
    # Send secure cookies only over HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Prevent browsers from guessing MIME types
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Referrer policy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
else:
    # Development settings (safe for localhost)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'