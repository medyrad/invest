from config.settings import *
DATABASES['default']['OPTIONS']['options'] = '-c statement_timeout=30000'
