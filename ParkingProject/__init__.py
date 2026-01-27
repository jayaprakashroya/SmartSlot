# PyMySQL shim to provide MySQLdb interface when mysqlclient is unavailable
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except Exception:
    # If pymysql is not installed yet, Django will raise an import error later.
    pass
