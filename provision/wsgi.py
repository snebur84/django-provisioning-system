import os
import pymysql # Importe o PyMySQL
pymysql.install_as_MySQLdb() # Força o PyMySQL a se passar por MySQLdb

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "provision.settings")

application = get_wsgi_application()