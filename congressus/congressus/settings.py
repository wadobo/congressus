"""
Django settings for congressus project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from os import environ as env
from zoneinfo import ZoneInfo

from django.contrib.messages import constants as messages


def env_list(env_name, default=list):
    """
    Get environment var and convert in python list. Example .env: APPS=x1,y2,z3
    """
    list_vars = env.get(env_name, None)
    return list_vars.split(',') if list_vars else default


def env_get_admins():
    """ Example: Foo:foo@test.com,Bar:bar@test.com """
    res = list()
    list_vars = env.get('ADMINS', '')
    admins = list_vars.split(',') if list_vars else list()
    for adm in admins:
        res.append(tuple(adm.split(':')))
    return tuple(res)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

SECRET_KEY = env.get('SECRET_KEY', 'v!r#8-@k_be__nior8(nwst!s&s$51+qu+^^(04q3w!nd1v_u9')

DEBUG = env.get('DEBUG', 'True') == 'True'
ADMINS = env_get_admins()
MANAGERS = ADMINS

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', [])


# Application definition

INSTALLED_APPS = [
    'custom_admin.apps.CustomAdminConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.flatpages',

    # 3rd party
    'crispy_forms',
    'maintenancemode',
    'tinymce',

    # custom apps
    'adminmenu',
    'tickets',
    'events',
    'mywebsocket',
    'windows',
    'access',
    'dashboard',
    'invs',
    'singlerow',

    # 3rd party, here to override templates
    'extended_filters',
    'django_admin_listfilter_dropdown',
]

SITE_ID = 1

MIDDLEWARE = (
    'congressus.suspicious_middleware.SuspiciousMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'middlewares.FixMaintenanceDup',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'congressus.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.filesystem.Loader',
            ]
        },
    },
]

WSGI_APPLICATION = 'congressus.wsgi.application'


# Database

config_database = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(BASE_DIR, env.get('DB_NAME', 'db.sqlite3')),
}

if env.get('DB_ENGINE', None):
    config_database = {
        'ENGINE': env.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': env.get('DB_NAME', 'geas'),
        'USER': env.get('DB_USER', 'geas'),
        'PASSWORD': env.get('DB_PASSWORD', 'geas'),
        'HOST': env.get('DB_HOST', 'db'),
        'PORT': env.get('DB_PORT', '5432'),
    }

DATABASES = {'default': config_database}

# Internationalization

LANGUAGE_CODE = env.get('LANGUAGE_CODE', 'en-us')

TIME_ZONE = 'Europe/Madrid'
TZINFO = ZoneInfo(TIME_ZONE)

USE_I18N = True

USE_L10N = True

USE_TZ = True

USE_THOUSAND_SEPARATOR = True

LOCALE_PATHS = (BASE_DIR + '/locale', )

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

CRISPY_TEMPLATE_PACK = 'bootstrap3'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = env.get('STATIC_URL', '/static/static/')
STATIC_ROOT = env.get('STATIC_ROOT', None)
MEDIA_URL = env.get('MEDIA_URL', '/static/media/')
MEDIA_ROOT = env.get('MEDIA_ROOT', os.path.join(BASE_DIR, 'static/media'))

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

CSRF_FAILURE_VIEW = 'tickets.views.csrf_failure'
CSRF_COOKIE_SECURE = env.get('CSRF_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SAMESITE = env.get('CSRF_COOKIE_SAMESITE', 'strict')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', [])
CSRF_COOKIE_MASKED = env.get('CSRF_COOKIE_MASKED', 'True') == 'True'

INTERNAL_IPS = ['127.0.0.1']


# Email

SERVER_EMAIL = env.get('EMAIL_SERVER', 'congressus@localhost')
FROM_EMAIL = env.get('FROM_EMAIL', 'congressus@localhost')
DEFAULT_FROM_EMAIL = env.get('EMAIL_DEFAULT', 'congressus@localhost')
EMAIL_BACKEND = env.get('EMAIL_BACKEND', 'django.core.mail.backends.filebased.EmailBackend')
EMAIL_FILE_PATH = '.mails'
EMAIL_HOST = env.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = env.get('EMAIL_PORT', 25)
EMAIL_HOST_USER = env.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env.get('EMAIL_USE_TLS', 'False') == 'True'


# CUSTOM SETTINGS

ORDER_SIZE = int(env.get('ORDER_SIZE', '15'))

# REDSYS TPV options
REDSYS_ENABLED = env.get('REDSYS_ENABLED', 'True') == 'True'
TPV_TERMINAL = env.get('TPV_TERMINAL', 1)
TPV_MERCHANT = env.get('TPV_MERCHANT', 'XXXXXX')
TPV_URL = env.get('TPV_URL', "https://sis-t.redsys.es:25443/sis/realizarPago")
# LANGS: Spanish - 001, English - 002
TPV_LANG = env.get('TPV_LANG', '002')
TPV_KEY = env.get('TPV_KEY', "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
TPV_MERCHANT_URL = env.get('TPV_MERCHANT_URL', '/ticket/confirm/')

# PAYPAL
PAYPAL_ENABLED = env.get('PAYPAL_ENABLED', 'False') == 'True'
PAYPAL_SANDBOX = env.get('PAYPAL_SANDBOX', 'True') == 'True'
PAYPAL_CLIENTID = env.get('PAYPAL_CLIENTID', 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
PAYPAL_SECRET = env.get('PAYPAL_SECRET', 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')

# STRIPE
STRIPE_ENABLED = env.get('STRIPE_ENABLED', False)
STRIPE_PK = env.get('STRIPE_PK', 'pk_live_xxxxxxxxxxxxxxxxxxxxxxxx')
STRIPE_SK = env.get('STRIPE_SK', 'sk_live_xxxxxxxxxxxxxxxxxxxxxxxx')
STRIPE_NAME = env.get('STRIPE_NAME', 'No es magia es Wadobo S.L.L.')
STRIPE_DESC = env.get('STRIPE_DESC', '')
STRIPE_IMAGE = env.get('STRIPE_IMAGE', 'https://s3.amazonaws.com/stripe-uploads/acct_103f1h2csBUWpoVVmerchant-icon-713198-wadobo-icon.png')
STRIPE_BITCOIN = env.get('STRIPE_BITCOIN', False)

QRCODE = True
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
DOMAIN = env.get('DOMAIN', 'congressus.local')
WS_SERVER = f'ws.{DOMAIN}'
TIMESTEP_CHART = 'daily'
MAX_STEP_CHART = 10

INVITATION_ORDER_START = '01'

MAX_SEAT_BY_SESSION = 50
EXPIRED_SEAT_H = 5*60 # 5 minutes
EXPIRED_SEAT_C = 15*60 # 15 minutes
EXPIRED_SEAT_P = 35*60 # TPV expired: 35 minutes

ROW_RAND = 3

ACCESS_VALIDATE_INV_HOURS = env.get('ACCESS_VALIDATE_INV_HOURS', 'True') == 'True'

TINYMCE_DEFAULT_CONFIG = {
    "height": 400,
    "width": "100%",
    "plugins": "code advlist link image lists",
    "force_br_newlines": True,
    "force_p_newlines": False,
    "forced_root_block": False,
    "verify_html": False,
    "extended_valid_elements": "*[*]",
    "toolbar": (
        "code | undo redo | styleselect | bold italic | alignleft aligncenter "
        "alignright alignjustify | bullist numlist outdent indent | link image",
    ),
}

REAL_EXTRA_APPS = []

SINGLEROW_MS = 5000
SINGLEROW_LANG = env.get('SINGLEROW_LANG', 'en')

if os.path.exists(os.path.join(BASE_DIR, 'theme')):
    print("Custom theme found... Using it")
    INSTALLED_APPS = ['theme'] + INSTALLED_APPS
    try:
        from theme.settings import *
        REAL_EXTRA_APPS += [i for i in EXTRA_APPS if i not in REAL_EXTRA_APPS]
    except Exception:
        pass

if REAL_EXTRA_APPS:
    INSTALLED_APPS += [i for i in REAL_EXTRA_APPS if i not in INSTALLED_APPS]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'session_cache',
    }
}
CSV_TICKET_FIELDS = env_list('CSV_TICKET_FIELDS', [])

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Debug toolbar options
DEBUG_TOOLS = env.get('DEBUG_TOOLS', 'True') == 'True'
if DEBUG and DEBUG_TOOLS:
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True,
        "SHOW_COLLAPSED": True,
    }

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]

    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    MIDDLEWARE = (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ) + MIDDLEWARE

    for tmpl in TEMPLATES:
        tmpl['OPTIONS']['context_processors'] = ['django.template.context_processors.debug'] + tmpl['OPTIONS']['context_processors']
