
##LOGGING
import logging, datetime
log = logging.getLogger(__name__)


##POSTGRES
try:
    import psycopg2
except ImportError:
    psycopg2 = None
    log.warning("Psycopg2 not installed. Postgres-based db types will be unavailable. (Try running 'pip install psycopg2')")

##EXCEPTION
class ConfigurationError(Exception):
    pass

##MAIN
class Environment():
    def __init__(self, db_type, db_name, db_address=None, db_user=None, db_pass=None, uuid=None, datetime_fmt="%Y-%m-%d %H:%M:%S"):

        self.db_type = db_type
        self.db_name = db_name
        self.db_address = db_address
        self.db_user = db_user
        self.db_pass = db_pass
        self.UUID = uuid
        self.DATETIME_FORMAT = datetime_fmt

        #INIT DB
        getattr(self, '_init_%s_' % self.db_type)()
    
    def _init_pg_odoo_(self):

        if not psycopg2:
            raise ImportError("Module psycopg2 is required for postgres db type!")

        try:
            self._connection = psycopg2.connect("dbname='{}' host='{}' user='{}' password='{}'".format(self.db_name,
                                                                                                       self.db_address,
                                                                                                       self.db_user,
                                                                                                       self.db_pass))
        except psycopg2.OperationalError as e:
            log.critical("Could not connect to DB_NAME '%s', DB_TYPE 'pg_odoo', CREDENTIALS %s:*****.\n%s" % (self.db_name, self.db_user, str(e)))
            raise e

        cur = self._connection.cursor()

        try:
            cur.execute("select workcenter_id, loss_id, cycles, nominal_cycle, date_start, date_end, duration from mrp_workcenter_productivity where false")
        except psycopg2.ProgrammingError as e:
            log.critical("Connection test with DB_TYPE 'pg_odoo' returned wrong table structure! Exception: " + str(e))
            raise e

        cur.close()


    #QUERIES
    def insert(self, obj, query, integrity_check=lambda x: None, fetch=False):
        keys = "(%s)" % ",".join(query.keys())
        values = list()
        
        for i in query.values():
            vtype = type(i)
            if vtype == datetime.datetime:
                values.append("'%s'" % i.strftime(self.DATETIME_FORMAT))

            elif vtype == bool:
                if i:
                    values.append('true')
                else:
                    values.append('false')

            elif vtype in [int, float, str]:
                values.append(str(i))

            else:
                raise TypeError("Cannot transform type {} to SQL type!".format({vtype}))

        values = "(%s)" % ",".join(values)

        query = "INSERT INTO {} {} VALUES {};".format(obj, keys, values)

        cur = self._connection.cursor()
        cur.execute(query)

        if integrity_check:
            try:
                integrity_check(cur)
                self._connection.commit()
            except Exception as e:
                log.exception(e)
                log.warning("Rolling back transaction with failed integrity check!")
                self._connection.rollback()
        else:
            self._connection.commit()

        cur.close()
        del cur


    #DATA LOAD
    def get_signal_raw(self):
        query = "SELECT from_coil, signal_type, name, id FROM mrp_workcenter_signal;"
        cur = self._connection.cursor()

        cur.execute(query)
        result = cur.fetchall()

        return result


ENVIRONMENT = None

def initENV(db_type, db_name, **kwargs):
    global ENVIRONMENT
    ENVIRONMENT = Environment(db_type, db_name, **kwargs)


def getEnv():
    global ENVIRONMENT
    if ENVIRONMENT:
        return ENVIRONMENT
    
    raise EnvironmentError("Environment not initialized!")
