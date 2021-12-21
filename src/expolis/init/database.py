import psycopg2


class Database:
    def __init__ (self):
        with open ('/opt/expolis/etc/config-database', 'r') as fd:
            database = fd.readline () [:-1]
            username = fd.readline () [:-1]
            password = fd.readline () [:-1]
        self.connection = psycopg2.connect (
            dbname=database,
            user=username,
            password=password
        )  # type: psycopg2.extensions.connection
        self.cursor = self.connection.cursor ()  # type: psycopg2.extensions.cursor

    def __del__ (self):
        self.cursor.close ()
        self.connection.commit ()
        self.connection.close ()
