from django.db.backends import BaseDatabaseIntrospection

class DatabaseIntrospection(BaseDatabaseIntrospection):
    # Maps type codes to Django Field types.
    data_types_reverse = {
        16: 'BooleanField',
        21: 'SmallIntegerField',
        23: 'IntegerField',
        25: 'TextField',
        700: 'FloatField',
        701: 'FloatField',
        869: 'IPAddressField',
        1043: 'CharField',
        1082: 'DateField',
        1083: 'TimeField',
        1114: 'DateTimeField',
        1184: 'DateTimeField',
        1266: 'TimeField',
        1700: 'DecimalField',
    }
        
    def get_table_list(self, cursor):
        "Returns a list of table names in the current database."
        cursor.execute("""
            SELECT t.tabname
            FROM systables t
            WHERE t.tabtype = 'T'
            """)
        return [row[0] for row in cursor.fetchall()]

    def get_table_description(self, cursor, table_name):
        "Returns a description of the table, with the DB-API cursor.description interface."
        cursor.execute("SELECT LIMIT 1 * FROM %s" % self.connection.ops.quote_name(table_name))
        return cursor.description

    def get_indexes(self, cursor, table_name):
        """
        Returns a dictionary of fieldname -> infodict for the given table,
        where each infodict is in the format:
            {'primary_key': boolean representing whether it's the primary key,
             'unique': boolean representing whether it's a unique index}
        """
        # This query retrieves each index on the given table, including the
        # first associated field name
        # ToDo: get primary and unique index info
        cursor.execute("""
            SELECT i.idxname, 0, 0
            FROM sysindexes i, systables t
            WHERE i.tabid = t.tabid
                AND t.tabname = %s""", [table_name])
        indexes = {}
        for row in cursor.fetchall():
            if ' ' in row[1]:
                continue
            indexes[row[0]] = {'primary_key': row[1], 'unique': row[2]}
        return indexes

