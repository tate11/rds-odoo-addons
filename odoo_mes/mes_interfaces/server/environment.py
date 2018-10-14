
##LOGGING
import logging, datetime
from xmlrpc import client as xcl
log = logging.getLogger(__name__)

##EXCEPTION
class ConfigurationError(Exception):
    pass

##MAIN
class Environment():
    def __init__(self, url, db, user=None, password=None, datetime_fmt="%Y-%m-%d %H:%M:%S"):

        self.url = url
        self.user = user
        self.password = password
        self.db = db

        self.DATETIME_FORMAT = datetime_fmt 

        self.common = xcl.ServerProxy('{}/xmlrpc/2/common'.format(url))
        self.models = xcl.ServerProxy('{}/xmlrpc/2/object'.format(url))

        self.uid = self.common.authenticate(db, user, password, {})
        if not self.uid:
            raise ValueError

    #QUERIES
    def execute(self, model, method, vals=None):
        return self.models.execute_kw(self.db, self.uid, self.password,
                                model, method, vals and [vals] or [[]])

ENVIRONMENT = None

def initENV(url, db, **kwargs):
    global ENVIRONMENT
    ENVIRONMENT = Environment(url, db, **kwargs)


def getEnv():
    global ENVIRONMENT
    if ENVIRONMENT:
        return ENVIRONMENT
    
    raise EnvironmentError("Environment not initialized!")
