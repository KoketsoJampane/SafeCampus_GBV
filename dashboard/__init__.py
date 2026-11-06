import pymysql

# Pretend we have the newer pymysql version Django wants
pymysql.version_info = (2, 2, 1, "final", 0) 

# Pretend we have MySQL 8.4 so Django stops crying
pymysql.install_as_MySQLdb()

from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.check_database_version_supported = lambda self: None 