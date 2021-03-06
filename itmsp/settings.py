"""
Django settings for itmsp project.

Generated by 'django-admin startproject' using Django 1.11.20.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""
import ConfigParser
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# read config file
CONFIG_FILE = os.path.join(BASE_DIR, 'itmsp.conf')
config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)

# base config
KEY = config.get('base', 'key')
LOCAL_HOST = config.get('base', 'host')
LOCAL_PORT = config.get('base', 'port')

# log config
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOG_LEVEL = config.get('base', 'log')

# database config
DB_HOST = config.get('db', 'host')
DB_PORT = config.get('db', 'port')
DB_USER = config.get('db', 'user')
DB_PASSWORD = config.get('db', 'password')
DB_DATABASE = config.get('db', 'database')

# cache config
CACHE_LOCATION = config.get('cache', 'location')
CACHE_KEY_PREFIX = config.get('cache', 'key_prefix')

# auth config
AUTH_USER_MODEL = 'iuser.ExUser'
AUTH_MODE = config.get('auth', 'auth_mode')
AUTH_MODE_MAP = {
    'basic': 'rest_framework.authentication.BasicAuthentication',
    'token': 'itmsp.authentication.CacheTokenAuthentication',
}

# remote_dir config
REMOTE_LOGDIR = config.get('remote', 'log_dir')

TOKEN_TMOUT = 3600
AAM_TMOUT = 30

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'j2brb@nhtw2t9pg!v$@+9n5_e)dlkg0$z&1&%x_g2sh#84b&sn'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # from other frameworks
    # 'djcelery',
    # 'kombu.transport.django',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'djcelery'
]

FUNC_APPS = [
    'itmsp',
    'iuser',
    'ivmware',
    'iworkflow',
    'iconfig',
    'iservermenu'
]

INSTALLED_APPS += FUNC_APPS

MIDDLEWARE = [
    'iconfig.middleware.InterfaceMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'itmsp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'itmsp.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_DATABASE,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

# Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': CACHE_LOCATION,
        'VERSION': '',
        'KEY_PREFIX': CACHE_KEY_PREFIX,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer'
        },
    },
}

# rest framework

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        AUTH_MODE_MAP[AUTH_MODE],
    )
}

# cors headers
CORS_ORIGIN_ALLOW_ALL = True

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

# LANGUAGE_CODE = 'zh-hans'
LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = False

USE_TZ = True

DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

IVM = {
    'VM_PREFIX_KEY': 'vm_prefix',
    'RESOURCE_LIMIT_MEM': 98,
    'RESOURCE_LIMIT_DS': 90,
    'RESOURCE_BAN_DS': ['share'],
    'LNX_SSH_SYS_USER': 'sysop',
    'LNX_SSH_USE_PWD': False,
    'LNX_SSH_PWD': '',
    'LINUX_CUSTOM_SPEC_NAME': "sles_118.240.13.0/24",
    "WINDOWS_CUSTOM_SPEC_NAME": "win2012_118.240.14.0/24"
}
