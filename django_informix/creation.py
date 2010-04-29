from django.conf import settings
from django.db.backends.creation import BaseDatabaseCreation
from django.core.management import call_command

class DatabaseCreation(BaseDatabaseCreation):
    # This dictionary maps Field objects to their associated Informix column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__ before being output.
    # If a column type is set to None, it won't be included in the output.
    data_types = {
        'AutoField':         'serial',
        'BooleanField':      'boolean',
        'CharField':         'varchar(%(max_length)s)',
        'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
        'DateField':         'date',
        'DateTimeField':     'datetime year to fraction(5)',
        'DecimalField':      'decimal(%(max_digits)s, %(decimal_places)s)',
        'FileField':         'varchar(%(max_length)s)',
        'FilePathField':     'varchar(%(max_length)s)',
        'FloatField':        'double precision',
        'IntegerField':      'integer',
        'IPAddressField':    'varchar(15)',
        'NullBooleanField':  'boolean',
        'OneToOneField':     'integer',
        'PositiveIntegerField': 'integer',
        'PositiveSmallIntegerField': 'smallint',
        'SlugField':         'varchar(%(max_length)s)',
        'SmallIntegerField': 'smallint',
        'TextField':         'lvarchar(1600)',
        'TimeField':         'interval hour to second',
    }

    def sql_table_creation_suffix(self):
        return ''

    def create_test_db(self, verbosity=0, autoclobber=None):
        """A fake create. The database must exist, we just drop any existing
        tables and call syncdb to create tables for default base database"""
        print "Preparing database..."
        database = settings.DATABASE_NAME
        self._drop_all_tables(self.connection.cursor())
        call_command('syncdb', database=self.connection, verbosity=verbosity, interactive = False)
        return database

    def destroy_test_database(self, database_name, verbository=0):
        """We do nothing here"""
        print "Destroying database..."
        return database_name
        
    def _drop_all_tables(self, cursor):
        tables = self.connection.introspection.django_table_names(only_existing=True)
        for table in tables:
            sql = "DROP TABLE %s" % self.connection.ops.quote_name(table)
            cursor.execute(sql)
        cursor.close()

    def sql_for_pending_references(self, model, style, pending_references):
        """Returns any ALTER TABLE statements to add constraints after the fact.
         Since informix foreign key constraint syntax doesn't support named 
         constraints we need to override default method"""
        from django.db.backends.util import truncate_name

        if not model._meta.managed or model._meta.proxy:
            return []
        qn = self.connection.ops.quote_name
        final_output = []
        opts = model._meta
        if model in pending_references:
            for rel_class, f in pending_references[model]:
                rel_opts = rel_class._meta
                r_table = rel_opts.db_table
                r_col = f.column
                table = opts.db_table
                col = opts.get_field(f.rel.field_name).column
                final_output.append(style.SQL_KEYWORD('ALTER TABLE') + ' %s ADD CONSTRAINT FOREIGN KEY (%s) REFERENCES %s (%s)%s;' % \
                    (qn(r_table),
                    qn(r_col), qn(table), qn(col),
                    self.connection.ops.deferrable_sql()))
            del pending_references[model]
        return final_output
