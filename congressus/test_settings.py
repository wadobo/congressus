from congressus.settings import *


STATIC_ROOT = '/tmp/static/static/'
MEDIA_ROOT = '/tmp/static/media/'

INSTALLED_APPS.remove('theme')

MIGRATION_MODULES = {
    'windows': 'windows.migrations_test',
}
