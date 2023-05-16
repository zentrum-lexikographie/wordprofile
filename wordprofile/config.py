from starlette.config import Config
from starlette.datastructures import Secret

config = Config(".env")

DEBUG = config('WP_DEBUG', cast=bool, default=False)

SPEC = config('WP_SPEC', default='spec/config.json')

DATA_DIR = config('WP_DATA_DIR', default='wp-data')

DB_HOST = config('WP_DB_HOST', default='localhost')
DB_NAME = config('WP_DB_NAME', default='wp')
DB_USER = config('WP_DB_USER', default='wp')
DB_PASSWORD = config('WP_DB_PASSWORD', cast=Secret, default='wp')

HTTP_HOSTNAME = config('WP_HTTP_HOSTNAME', default='0.0.0.0')
HTTP_PORT = config('WP_HTTP_PORT', cast=int, default=8086)
XML_RPC_PORT = config('WP_XML_RPC_PORT', cast=int, default=8086)

MIN_REL_FREQ = config('WP_MIN_REL_FREQ', cast=int, default=3)

MWE = config('WP_MWE', cast=bool, default=False)
