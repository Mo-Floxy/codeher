"""PyMySQL stands in for mysqlclient so no C toolchain is needed on Windows."""

try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # sqlite test runs and non-MySQL engines do not need it
    pass
