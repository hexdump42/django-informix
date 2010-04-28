import os
import sys

from django.db.backends import BaseDatabaseClient

class DatabaseClient(BaseDatabaseClient):
    executable_name = 'dbaccess'

    def runshell(self):
        settings_dict = self.connection.settings_dict
        args = [self.executable_name]
        args += [settings_dict['DATABASE_NAME']]
        if os.name == 'nt':
            sys.exit(os.system(" ".join(args)))
        else:
            os.execvp(self.executable_name, args)

