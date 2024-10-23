from pathlib import Path
from decouple import config
from celery.schedules import crontab
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", cast=bool)

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://e3b6-2405-201-3027-e01e-ed0a-da6a-6541-11b3.ngrok-free.app', 
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # rest_framework_api
    "rest_framework",
    "rest_framework.authtoken",
    # django_app
    "accounts",
    "vendor",
    "menu",
    "marketplace",
    "customers",
    'orders'
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "foodOnline_main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.get_vendor",
                "marketplace.context_processors.get_cart_counter",
                "marketplace.context_processors.get_cart_amounts",
                'accounts.context_processors.get_user_profile',

            ],
        },
    },
]

WSGI_APPLICATION = "foodOnline_main.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fooddb",
        "USER": "user",
        "PASSWORD": "123",
        "HOST": "localhost",  
        "PORT": "5432",  
    }
}

AUTH_USER_MODEL = "accounts.User"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_DIRS = [
    "foodOnline_main/static",
]

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



MESSAGE_TAGS = {
    messages.ERROR: "danger",
}

# Email configuration
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT", cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = "foodOnline Marketplace <shbkhan@bestpeers.com>"


# Rest_configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
    ),
}


STRIPE_PUBLISHABLE_KEY=config('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY=config('STRIPE_SECRET_KEY')
STRIPE_ENDPOINT_SECRET=config('STRIPE_ENDPOINT_SECRET') 


CELERY_BROKER_URL = 'redis://localhost:6380/0'


CELERY_BEAT_SCHEDULE = {
    'send-vendor-reports-every-minute': {
        'task': 'orders.tasks.send_vendor_reports',
        'schedule': crontab(), 
    },
}
