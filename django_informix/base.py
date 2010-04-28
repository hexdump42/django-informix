"""
Informix database backend for Django.

Requires Informix IDS 11.x, CLiSDK, & informixdb 2.5
"""

autocommit = True

from django.db.backends import *
from django.db.backends.signals import connection_created
from django_informix.client import DatabaseClient
from django_informix.creation import DatabaseCreation
from django_informix.introspection import DatabaseIntrospection
#from django_informix.version import get_version
from django.utils.encoding import smart_str, smart_unicode

import datetime
try:
    import mx.DateTime
except ImportError:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured, "Error loading mx.DateTime module"

import re
# RE for datetime of format YYYY-MM-DD HH:MM:SS.FFFFFF
re_datetime_with_fraction6 = re.compile("^\d{4}-\d{2}-\d{2}\s\d{2}\:\d{2}\:\d{2}\.\d{6}$")
# RE for datetime of format YYYY-MM-DD HH:MM:SS
re_datetime_no_fraction = re.compile("^\d{4}-\d{2}-\d{2}\s\d{2}\:\d{2}\:\d{2}$")
# RE's to find LIMIT & OFFSET in query
re_limit = re.compile("(?P<lkey>\LIMIT?)\s(?P<lvalue>\d*?)$")
re_offset = re.compile("(?P<okey>\OFFSET?)\s(?P<ovalue>\d*?)$")

try:
    import informixdb as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading informixdb module: %s" % e)

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError

class FixCursorWrapper(object):
    """
    A thin wrapper around informixdb cursors that "fixes" them to work with
    django.

        1. allows them to accept Unicode strings as params.

           If a param is Unicode, this will convert it to a bytestring using 
           database client's encoding before passing informixdb.

           All results retrieved from the database are converted into Unicode
           strings before being returned to the caller.

        2. Django uses "format" (e.g. '%s') style placeholders, but informixdb
           uses '?' style.
           
           Convert to ? style, but if you want to use literal '%s' in a query
           you'll need to use '%%s'.

        3. Sets lastrowid using sqlerrd[1]
    """
    def __init__(self, cursor, charset):
        self.cursor = cursor
        self.charset = charset
        self.lastrowid = None

    def format_params(self, params):
        if isinstance(params, dict):
            result = {}
            charset = self.charset
            for key, value in params.items():
                result[smart_str(key, charset)] = smart_str(value, charset)
            return result
        else:
            return tuple([smart_str(p, self.charset, True) for p in params])

    def execute(self, sql, params=()):
        if len(params) > 0: 
            params = self._fix_datetime(params)
        sql = self._convert_placeholders(sql)
        sql = self._fix_sql(sql)
        results = self.cursor.execute(smart_str(sql, self.charset), self.format_params(params))
        self.lastrowid = self.cursor.sqlerrd[1]
        return results

    def executemany(self, sql, param_list):
        sql = self._convert_placeholders(sql)
        sql = self._fix_sql(sql)
        if len(params) > 0: 
            params = self._fix_datetime(params)
        new_param_list = [self.format_params(params) for params in param_list]
        results = self.cursor.executemany(sql, new_param_list)
        self.lastrowid = self.cursor.sqlerrd[1]
        return results

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchmany(self, rows=Database.Cursor.arraysize):
        return self.cursor.fetchmany(rows)

    def _convert_placeholders(self, query):
        # replace occurances of "%s" with "?" 
        return query.replace("%s","?")

    def _fix_datetime(self, params):
        # convert datetime so informixdb can handle them
        params = list(params)
        for i in range(0,len(params)):
            p = str(params[i])
            if type(params[i]) == type(datetime.datetime.now()):
                params[i] = p[:-1]
            else:
                # Check to see if it's a datetime string with fraction 6
                if re_datetime_with_fraction6.match(p) is not None:
                    params[i] = p[:-1]
                elif re_datetime_no_fraction.match(p) is not None:
                    dt = mx.DateTime.strptime(p, "%Y-%m-%d %H:%M:%S")
                    params[i] = Database.TimestampFromTicks(dt.ticks())
        return tuple(params)

    def _fix_sql(self, query):
        # Remove LIMIT keyword if present
        i = query.find(" LIMIT")
        limit_offset = query[i:]
        if i > -1:
            query = query[0:i+1]
            # Use informix SKIP LIMIT instead
            r = re_limit.search(limit_offset)
            limit = "LIMIT %s" % r.groupdict()['lvalue']
            r = re_offset.search(limit_offset)
            if r is not None:
                skip = "SKIP %s" % r.groupdict()['ovalue']
            else:
                skip = ""
            i = query.find("SELECT ")
            q = []
            q.append("SELECT ")
            q.append(skip)
            q.append(limit)
            q.append(query[7:])
            query = " ".join(q)
        return query

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

class DatabaseFeatures(BaseDatabaseFeatures):
    uses_savepoints = False
    uses_autocommit = autocommit

class DatabaseWrapper(BaseDatabaseWrapper):
    operators = {
        'exact': '= %s',
        'iexact': '= UPPER(%s)',
        'contains': 'LIKE %s',
        'icontains': 'LIKE UPPER(%s)',
        'regex': '~ %s',
        'iregex': '~* %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'endswith': 'LIKE %s',
        'istartswith': 'LIKE UPPER(%s)',
        'iendswith': 'LIKE UPPER(%s)',
    }

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.features = DatabaseFeatures()
        self.ops = DatabaseOperations()
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation()

    def _cursor(self):
        from django.conf import settings
        settings_dict = self.settings_dict
        if self.connection is None:
            if settings_dict['DATABASE_NAME'] == '':
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("You need to specify DATABASE_NAME in your Django settings file.")
            dbname = settings_dict['DATABASE_NAME']
            dbauth = {}
            if settings_dict['DATABASE_USER']:
                dbauth['user'] = settings_dict['DATABASE_USER']
            if settings_dict['DATABASE_PASSWORD']:
                dbauth['password'] = settings_dict['DATABASE_PASSWORD']
            # ToDo: Consider how to apply DATABASE_OPTIONS
            self.connection = Database.connect(dbname, **dbauth)
            connection_created.send(sender=self.__class__)
            self.connection.autocommit = autocommit
        cursor = self.connection.cursor()
        if settings.DEBUG:
            return util.CursorDebugWrapper(FixCursorWrapper(cursor, 'utf-8'), self)
        cursor = FixCursorWrapper(cursor, 'utf-8')
        return cursor

    def start_transaction_sql(self):
        """
        Returns the SQL statement required to start a transaction.
        """
        return "BEGIN WORK;"

def typecast_string(s):
    """
    Cast all returned strings to unicode strings.
    """
    if not s and not isinstance(s, str):
        return s
    return smart_unicode(s)

#Database.register_type(Database.new_type(Database.types[1043].values, 'STRING', typecast_string))


class DatabaseOperations(BaseDatabaseOperations):
    def quote_name(self, name):
        # Informix does not support quoted table or column names
        return name
        if name.startswith('"') and name.endswith('"'):
            return name # Quoting once is enough.
        return '"%s"' % name

