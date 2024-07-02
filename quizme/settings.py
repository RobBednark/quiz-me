import os

# Django settings for quizme project.

AUTH_USER_MODEL = 'emailusername.User'

BASEDIR = os.path.abspath(os.path.dirname(__file__))
DEBUG = eval(os.environ.get('QM_DEBUG', 'True'))
ENABLE_DJANGO_DEBUG_TOOLBAR = eval(os.environ.get('QM_USE_TOOLBAR', 'False'))

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Default database engine to postgres, but can override with QM_ENGINE=sqlite
engine = 'django.db.backends.postgresql_psycopg2'
if (os.environ.get('QM_ENGINE', None) == 'sqlite'):
    engine = 'django.db.backends.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': engine,
        'NAME': os.environ.get('DB_QUIZME', 'quizme_default_db'),
        # The following settings are not used with sqlite3:
        'USER': os.environ.get('DB_USER', 'quizme'), # Set to empty string for default.
        'PASSWORD': os.environ.get('QM_DB_PASSWORD', ''),
        'HOST': os.environ.get('QM_DB_HOST', 'localhost'), # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': os.environ.get('QM_DB_PORT', ''), # Set to empty string for default.
        'TEST': {
            # If ENGINE is sqlite, and NAME is None, then in-memory sqlite
            # db will be used, else a file-based sqlite db will be used.
            'NAME': os.environ.get('QM_TEST_DB', None),
        },
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

LOGIN_URL = '/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = BASEDIR + "/../static"

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASEDIR, 'static'),
)

# Custom Django-Pagedown CSS
PAGEDOWN_WIDGET_CSS = (
    '../static/pagedown/demo/browser/demo.css',
    '../static/pagedown/custom.css',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = ')ltnqpp5h)&r217dm)@4ia9bq)idd5+@jr19qz62!gh0sm@7-p'

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
if ENABLE_DJANGO_DEBUG_TOOLBAR:
    # Django Debug Toolbar (per the docs, make sure to put it first!)
    MIDDLEWARE = ('debug_toolbar.middleware.DebugToolbarMiddleware',) + MIDDLEWARE
ROOT_URLCONF = 'quizme.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'quizme.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',

    # imported apps:
    'pagedown',  # used for markdown editor
    'markdown_deux',  # for displaying markdown as html in a template

    # local apps:
    'questions',
    'emailusername',  # used for User; so email addresses can be used as username
)
if DEBUG:
    INSTALLED_APPS += ('django_extensions',)

def show_toolbar_callback(request):
    # This func is called by DEBUG_TOOLBAR_CONFIG['SHOW_TOOLBAR_CALLBACK']
    return ENABLE_DJANGO_DEBUG_TOOLBAR

if ENABLE_DJANGO_DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    DEBUG_TOOLBAR_CONFIG = {
        'PROFILER_MAX_DEPTH': 20,
        'SHOW_TOOLBAR_CALLBACK': 'quizme.settings.show_toolbar_callback',
    }

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# This is the default test runner.  Added here to suppress warnings after upgrade to Django 1.7
# Can probably be removed after upgrading to 1.10, as I read something that indicated Django
# was removing the warning.
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

INTERNAL_IPS = [
        '0.0.0.0',
        '127.0.0.1',  # needed for django_debug_toolbar
]

# Used by django-markdown-deux for the '|markdown' template tag
MARKDOWN_DEUX_STYLES = {
    "do-not-escape-html": {
        # Do not escape html tags, just leave them as is
        # (i.e., "unsafe" mode)
        "safe_mode": False,
    },
}

CSRF_TRUSTED_ORIGINS = [
    'http://0.0.0.0',
    'http://localhost',
    'http://*.bednark.org',
    'https://*.bednark.org',
]

try:
    # Simple way of allowing for custom local dev/testing settings
    from local_settings import *  # noqa
except ImportError:
    pass

# Set the default primiary-key field type for models that don't have a primary-key field explicitly set
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'