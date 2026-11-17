"""Public application policy on the isolated test DB; loopback HTTP transport only."""
from config.settings import *
assert INVEST_ENV == 'public'
assert DATABASES['default']['NAME'] == 'invest_browser'
SECURE_SSL_REDIRECT = False  # local test transport, never used by the application service
