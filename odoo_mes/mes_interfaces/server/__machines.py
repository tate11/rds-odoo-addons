from datetime import datetime as dt
from datetime import timedelta as td

import logging, json
from tools import DEFAULT_DT_FORMAT

log = logging.getLogger()

class MrpWorkcenter():

    def __init__(self, env, wcid, name, cycle_time=None, tolerance=0.2):
        self._env = env
        self._id = wcid

        self._name = name 
        self._cycle_time = cycle_time
        self._tolerance = tolerance
        self._default_status = 2

        self.cycles = 0    

        self.startDate = dt.now()
        self.endDate = None
        

        self.status = 2
        self.interval_id = None
        self.post()

    def still(self):
        self.status = self._default_status
        self.startDate = dt.now()
        self.endDate = None
        self.cycles = None

    def ping(self, force=False):
        if self.status == 2:       
            if force:
                self.post()
        else:
            newEnd = dt.now()
            delta = (newEnd - self.endDate).total_seconds()
            if delta >= self._cycle_time*(1+self._tolerance):
                self.post()
                self.still()

    def do_cycle(self):
        log.info('Battuta!')
        if self.status == 7:
            self.cycles += 1
            self.endDate = dt.now()
            self.post()
        else:
            self.endDate = dt.now()
            self.post(True)
            self.status = 7
            self.cycles += 1
            self.startDate = self.endDate
        return True
        
    def post(self, close=False):
        if self.interval_id:
            self._env.execute('''
                                UPDATE mrp_workcenter_productivity SET
                                loss_id={}, cycles={}, date_end='{}', duration={} WHERE id={};
                               '''.format(self.status, self.cycles,
                                          self.endDate.strftime(DEFAULT_DT_FORMAT), (self.endDate-self.startDate).total_seconds()/60,
                                          self.interval_id))
        if close:
            self.interval_id = None

        if not self.interval_id:
            self.interval_id = self._env.execute('''
                                                    INSERT INTO mrp_workcenter_productivity
                                                    (workcenter_id, loss_id, cycles, nominal_cycle, date_start) VALUES ({},{},{},{},'{}')
                                                    RETURNING id;
                                                  '''.format(self._id, self.status, self.cycles, self._cycle_time,
                                                             self.startDate.strftime(DEFAULT_DT_FORMAT)), True)[0][0]


    def set_values(self, **kwargs):
        self._cycle_time = kwargs.get('cycle_time', self._cycle_time)
        self._tolerance = kwargs.get('tolerance', self._tolerance)
        self.status = kwargs.get('status', self.status)


def load_machines(env):
    machines = dict()

    with open('data/workcenters.json') as json_data:
        data = json.load(json_data)

        for key in data:
            m = data[key]
            machines[m['id']] = MrpWorkcenter(env, m['id'], m['name'], m['cycle_time'], m['tolerance'])
    
    return machines