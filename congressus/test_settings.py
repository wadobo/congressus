from congressus.settings import *


STATIC_ROOT = '/tmp/static/static/'
MEDIA_ROOT = '/tmp/static/media/'

MIGRATION_MODULES = {
    'windows': 'windows.migrations_test',
}
