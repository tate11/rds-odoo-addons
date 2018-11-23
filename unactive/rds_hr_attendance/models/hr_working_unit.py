# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, AccessError, ValidationError

from datetime import datetime, date, time, timedelta

import math, pytz, logging, json

PAUSE_TOLLERANCE = timedelta(2/24)

#PARAMETRI PAGHE
SPDF = '%d/%m/%Y'
COMPANY_PAYROLL_CODE = '000199'

# TIME COMPUTATION 
def intrslice(inttup, intarrs2):
    pp_intervals = []
    for i in intarrs2:
        if inttup[0] >= i[1]:
            continue
        elif inttup[1] > i[1]:
            pp_intervals += [(max(inttup[0], i[0]), i[1])]
            inttup = (i[1], inttup[1])
        else:
            pp_intervals += [(max(inttup[0], i[0]), inttup[1])]
    return pp_intervals

def dtc2fwo(dt, dt2):
    return dt2.day - dt.day, dt2.hour + dt2.minute/60

def dtc2f(dt, dt2):
    return (dt2.day - dt.day)*24 + dt2.hour + dt2.minute/60

def td2fn(td, upper=True):
    if upper:
        return math.ceil((td.days*(24) + td.seconds/3600)*4.0)/4.0

    return ((td.days*(24) + td.seconds/3600) // 0.25 )*0.25

def timestring_to_timedelta(ts):
    h = ts[:2]
    t = ts[2:]
    if int(h) > 23:
        pass
    if int(t) > 59:
        pass 

    return timedelta( int(h)/24 + int(t)/(24*60) )


def float_to_timedelta(float_hour, normalize=False):
    if normalize == 'ceil':
        return timedelta((math.ceil(float_hour/0.25)*0.25)/24)
    if normalize == 'floor':
        return timedelta((math.floor(float_hour/0.25)*0.25)/24)

    return timedelta(float_hour/24)

def dt2foff(dt):
    wd = dt.weekday()
    time = dt.time()

    return 24*wd + time.hour + time.minute/60

def dtf2dt(field):
    return datetime.strptime(field, DEFAULT_SERVER_DATETIME_FORMAT)

def df2d(field):
    return datetime.strptime(field, DEFAULT_SERVER_DATE_FORMAT)

def d2dt(d, tz=False, inv=False):
    if tz:
        return ( pytz.utc.localize(datetime(d.year, d.month, d.day, 0, 0, 0)).astimezone(pytz.timezone(tz)) if inv 
                 else pytz.timezone(tz).localize(datetime(d.year, d.month, d.day, 0, 0, 0)) )
    else:
        return datetime(d.year, d.month, d.day, 0, 0, 0)

    
def dt2dtn(dt, tz=False, inv=False, ceil=True):
    if tz:
        a = pytz.utc.localize(datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0)).astimezone(pytz.timezone(tz)) if inv else pytz.timezone(tz).localize(datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0))
        return a + timedelta( (15*(math.ceil(dt.minute/15)) if ceil else 15*(math.floor(dt.minute/15)))/(1440) )
    else:
        return datetime(dt.year, dt.month, dt.day, dt.hour, 0, 0) + timedelta( (15*(math.ceil(dt.minute/15)) if ceil else 15*(math.floor(dt.minute/15)))/(1440) )

def dt2dtf(dt):
    try:
        return dt.astimezone(pytz.utc).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    except ValueError:
        return dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

def dt2df(dt):
    try:
        return dt.astimezone(pytz.utc).strftime(DEFAULT_SERVER_DATE_FORMAT)
    except ValueError:
        return dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

# OTHER COMPUTATION

def get_pause_duration(atts):
    if len(atts) <= 1:
        return 0
    else:
        pause = 0
        for i in range(1, len(atts)):
            pause += td2fn(dtf2dt(atts[i].check_in) - dtf2dt(atts[i-1].check_out))
        return pause

class HrWorkingUnitInterval(models.Model):
    _name = 'rds.hr.working.unit.interval'
    _order = 'time_from_o, time_from'

    name = fields.Char("Intervallo", compute="get_interval_name")

    working_unit_id = fields.Many2one('rds.hr.working.unit', string="Unità Lavorativa", required=True, readonly=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', related='working_unit_id.employee_id', store=True, readonly=True)

    date = fields.Date(string="Giornata", related='working_unit_id.date', store=True, readonly=True)

    time_from_o = fields.Integer(string="Giorno")
    time_from = fields.Float(string="Inizio")
   
    time_to_o = fields.Integer(string="Giorno")
    time_to = fields.Float(string="Fine")

    duration = fields.Float("Durata", compute="get_duration", store=True)
    qtimef = fields.Float("Tempo da qualificato", compute="get_fqft")
    qtimet = fields.Float("Tempo da qualificato", compute="get_fqft")

    reason = fields.Many2one("hr.holidays.status", 'Giustificativo')

    #REPORTISTICA
    department_id = fields.Many2one('hr.department', store=True, readonly=True)
    is_subworker = fields.Selection(selection=[
        ('true', 'Interinale'),
        ('false', 'Dipendente')],
        store=True, readonly=True, default="false")
    justification_category = fields.Selection(selection=[
        ('wh', 'Ore Ordinarie'),
        ('extra', 'Straordinari'),
        ('pleave', 'Permessi pagati'),
        ('inps', 'Assenze INPS'),
        ('unpaid', 'Non Pagato')
    ], store=True, related="reason.justification_category", string="Tipo Giustificativo")

    @api.multi
    def get_interval_name(self):
        for i in self:
            i.name = "[%s] %s: %s ore di %s" % (i.date, i.employee_id.name, str(i.duration), ("Ingiustificato" if not i.reason else i.reason.name))

    @api.model
    def create(self, vals):
        a = super(HrWorkingUnitInterval, self).create(vals)
        eid = a.employee_id
        
        a.is_subworker = "true" if eid.is_subworker else "false"
        a.department_id = eid.department_id.id
        return a

    @api.model
    def UPDATE_INTERVALS(self):
        for i in self.search([]):
            i.is_subworker = "true" if i.employee_id.is_subworker else "false"

    def get_fqft(self):
        for x in self:
            x.qtimet = int(x.time_to_o)*24 + float(x.time_to)
            x.qtimef = int(x.time_from_o)*24 + float(x.time_from)

    @api.depends('time_from_o', 'time_from', 'time_to_o', 'time_to')
    def get_duration(self):
        for i in self:
            i.duration = float(i.time_to) - float(i.time_from) + 24*int(i.time_to_o) - 24*int(i.time_from_o)

    @api.multi
    def get_reasons(self):
        reasons = []
        for i in self:
            if i.reason in reasons:
                continue
            reasons += [i.reason]
        return reasons

    @api.multi
    def get_total(self):
        total = 0.0
        for i in self:
            total += i.duration
        return total

    @api.multi
    def get_layouted_intervals(self, cumulate_wk=False):
        reasons = self.mapped(lambda x: x.reason)
        normal = []
        cumulated = []

        for i in reasons:
            normal += [[i, self.filtered(lambda x: x.reason == i).get_total(), 0]]

        if cumulate_wk:
            cumulated = [
                         ['Totale Lavorato', self.filtered(lambda x: getattr(x.reason, 'justification_category', False) in ['extra','wh']).get_total()],
                         ['di cui Straordinari', self.filtered(lambda x: getattr(x.reason, 'justification_category', False) == 'extra').get_total()],
                         ['Totale Assenze', self.filtered(lambda x: getattr(x.reason, 'justification_category', False) in ['inps', 'pleave']).get_total()]
                        ]
            return [cumulated, normal]
        else:
            return normal

    @api.multi
    def is_reason_absence(self):
        if self.reason:
            return int(self.reason.is_absence)
        return 0     
        
class HrWorkingUnit(models.Model):
    _name = 'rds.hr.working.unit'
    _rec_name = 'full_name'
    _order = 'date desc'

    @api.model
    def _get_computed_reason_ids(self):
        cmpreas = {}
        cmpreas['OLAV']         = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.olav.id'))

        cmpreas['EXTR']         = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.extr.id'))
        cmpreas['EXTR_NOTTE']   = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.extn.id'))
        cmpreas['EXTR_FESTIVO'] = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.extf.id'))

        cmpreas['MAGN_SERA']    = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.mags.id'))
        cmpreas['MAGN_NOTTE']   = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.magn.id'))
        cmpreas['MAGP_SERA']    = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.mgsp.id'))
        cmpreas['MAGP_NOTTE']   = int(self.env['ir.config_parameter'].sudo().get_param('holiday.status.id.cmpreas.mgnp.id'))

        return cmpreas
         
    @api.multi
    def _compute_full_name(self):
        for i in self:
            if bool(i.date) & bool(i.employee_id): 
                i.full_name = str(i.employee_id.name) + ' - ' + str(i.date)
            else:
                i.ful_name = 'Nuova'

    full_name = fields.Char(readonly=True, compute="_compute_full_name")

    employee_id = fields.Many2one('hr.employee', string="Impiegato", required=True)
    date = fields.Date(string="Giornata", required=True)
    working_schedule = fields.Many2one('resource.calendar', string="Scheda Oraria", required=True)
    extraordinary_policy = fields.Selection(selection=[
        ('fill_ignore', 'Flessibile'),
        ('fill_extr'  , 'Flessibile con Straordinari'),
        ('ignore'     , 'Rigido')
    ], required=True, default="ignore", string="Politica Orario", help="La politica da adottare in contabilizzazione per il lavoro fuori orario.")

    work_from = fields.Datetime(string="Lavora da", store=True, compute="_compute_working_schedule")
    work_to = fields.Datetime(string="Lavora a", store=True, compute="_compute_working_schedule")
    _worked_time = fields.Float(string="Lavoro Teorico",  store=True, compute="_compute_working_schedule" )

    needed_action = fields.Integer(string="Livello di azione richiesta", store=True, readonly=True)
    anomaly_type = fields.Selection(selection=[
        ('ia', 'Sono presenti intervalli aperti o nulli'),
        ('is', 'Sono presenti intervalli sovrapposti'),
        ('ii', 'Sono presenti intervalli senza giustificativo'),
        ('ie', 'Sono presenti straordiari non pagati'),
        ('oca','Sono presenti intervalli di assenza ma il totale giustificato supera le ore previste'),
        ('oho','Sono presenti straordinari giustificati come ore ordinarie.'),
        ('sp', 'Stai pagando degli straordinari'),
        ('spp', 'Stai pagando parzialmente gli straordinari')
    ], default=False, store=True, string="Anomalie", help="Errore che ha interrotto la computazione.")

    worked_time = fields.Float(string="Ore Giustificate", store=True, readonly=True)
    total_attended = fields.Float(string="Totale Presente", store=True, readonly=True)

    intervals_ids   = fields.One2many('rds.hr.working.unit.interval', 'working_unit_id', string="Intervalli")

    attendances_ids = fields.One2many('hr.attendance', 'working_unit_id', string="Timbrature", readonly=True)
    _attendances_ids = fields.One2many('resource.calendar.attendance', compute="_compute_working_schedule", readonly=True, string="Presenze nominali")
    holiday_ids     = fields.Many2many('hr.holidays', 'working_unit_holidays_rel', string="Assenze", store=True)

    declarations = fields.Text(string="Dichiarazioni")

    payroll_gis = fields.Text(string="GIS Busta Paga", store=True, readonly=True)

    ##Campi Relazionati
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True, readonly=True)

    #altri gg
    yesterday = fields.Many2one('rds.hr.working.unit',  store=False, compute='get_other_wus')
    tomorrow = fields.Many2one('rds.hr.working.unit', store=False, compute='get_other_wus')
    weekday = fields.Char(compute='get_weekday')

    def get_weekday(self):
        for i in self:
            date = df2d(i.date)
            i.weekday = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'][date.weekday()]

    def get_other_wus(self):
        date_n = dt2df(df2d(self.date) + timedelta(1))
        date_y = dt2df(df2d(self.date) - timedelta(1))
        self.tomorrow = self.env['rds.hr.working.unit'].search([('employee_id', '=', self.employee_id.ids[0]), ('date', '=', date_n)], limit=1)
        self.yesterday = self.env['rds.hr.working.unit'].search([('employee_id', '=', self.employee_id.ids[0]), ('date', '=', date_y)], limit=1)

    def do_nothing(self):
        return

    def pol_rig(self):
        self.extraordinary_policy = 'ignore'
        self.compute_payroll()

    def pol_flex(self):
        self.extraordinary_policy = 'fill_ignore'
        self.compute_payroll()

    def pol_flex_stra(self):
        self.extraordinary_policy = 'fill_extr'
        self.compute_payroll()

    def go_next(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'rds.hr.working.unit',
            'clear_breadcrumb': True,
            'target': 'main',
            'res_id': self.tomorrow.ids[0]
        }

    def go_main(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Situazione Mese Lavorativo',
            'view_mode': 'flaggrid,grid,list,form',
            'res_model': 'rds.hr.working.unit',
            'clear_breadcrumb': True,
            'target': 'main',
        }

    def go_prev(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'rds.hr.working.unit',
            'clear_breadcrumb': True,
            'target': 'main',
            'res_id': self.yesterday.ids[0]
        }
                

    def get_gis_payroll(self):
        for i in self:
            if (not i.employee_id.payroll_id) or (i.needed_action == 3):
                i.payroll_gis = False
                continue
            
            leadinfo = '000' + COMPANY_PAYROLL_CODE + '0001' + str(i.employee_id.payroll_id).zfill(6)

            reasons = i.intervals_ids.get_reasons()
            contab_string = ''

            for reason in reasons:
                if reason.payroll_code == False:
                    continue

                total = i.intervals_ids.filtered(lambda x: x.reason == reason).get_total()

                starting = ' '
                if reason.is_absence:
                    previous = i.env['rds.hr.working.unit'].search([('employee_id', '=', i.employee_id.ids[0]), ('date', '=', (df2d(i.date) - timedelta(1)).strftime(DEFAULT_SERVER_DATE_FORMAT)) ])
                    
                    if not previous:
                        starting = 'S'
                    elif previous.intervals_ids.filtered(lambda x: x.reason == reason):
                        starting = 'N'
                    else:
                        starting = 'S'
                contab_string = contab_string + leadinfo + reason.payroll_code.ljust(5) + datetime.strptime(i.date, DEFAULT_SERVER_DATE_FORMAT).strftime(SPDF) + 'H' + '0000000000' + str(int(total*100)).zfill(10) + '0000000000' + str(int(i._worked_time*100)).zfill(4) + 'G' + starting + '\n'

            i.payroll_gis = contab_string

    @api.multi
    @api.depends('working_schedule', 'date')
    def _compute_working_schedule(self):
        for i in self:
            if not(i.date):
                continue

            d = df2d(i.date)

            att = i.working_schedule._get_day_attendances(df2d(i.date), False, False).filtered(lambda x: x._get_previous_connected() == False).sorted(key=lambda n: (int(n.dayofweek)*24.0 + n.hour_from))
            if att:
                att = att[0].get_attendances_chain()
                wf = float_to_timedelta(att[0].hour_from)
                wt = float_to_timedelta(att[-1].hour_to)
                wfdt = d2dt(d, 'Europe/Rome').astimezone(pytz.utc) + wf
                wtdt = d2dt(d, 'Europe/Rome').astimezone(pytz.utc) + timedelta(int(att[-1].dayofweek) - int(att[0].dayofweek)) + wt
            else:
                wf = timedelta(0.5)
                wt = timedelta(0.5)
                wfdt = d2dt(d, 'Europe/Rome').astimezone(pytz.utc) + wf
                wtdt = d2dt(d, 'Europe/Rome').astimezone(pytz.utc) + wt

            td = wtdt - wfdt

            pause = 0.0
            for at in range(1, len(att)):
                pause += (att[at].hour_from - att[at - 1].hour_to) + 24.0*(int(att[at].dayofweek) - int(att[at-1].dayofweek))

            i.work_from = wfdt
            i.work_to = wtdt
            i._worked_time = (td.days*(3600*24) + td.seconds) / 3600 - pause
            i._attendances_ids = att

    def get_nominal_pause(self):
        pause = 0
        for i in range(0, (len(self._attendances_ids)-1)):
            pause += self._attendances_ids[i+1].hour_from - self._attendances_ids[i].hour_to + (int(self._attendances_ids[i+1].dayofweek) - int(self._attendances_ids[i].dayofweek))*24
        
        return pause

    def apply_bonus(self, intervals, absences):
        #self.env['ir.config.parameter'].get_param('name')
        bonus = self.employee_id.payroll_bonus
        reasons = self._get_computed_reason_ids()
        order = {'w':0,'e':1}
        
        def total(tuparray):
            total = 0
            for i in tuparray:
                total += i['to'] - i['from']
            return total
        
        if self.extraordinary_policy == 'ignore':
            _intervals = sorted([x for x in intervals if x['type'] == 'w'], key = lambda x: (order[x['type']]))
        if self.extraordinary_policy != 'ignore':
            _intervals = sorted(intervals, key = lambda x: (order[x['type']]))

        c_intervals = []

        while _intervals:
            i = _intervals.pop(0)
            if not i['code'].calc:
                c_intervals += [i]
                continue

            if (i['type'] == 'e') & (total(c_intervals) >= self._worked_time) & (self.extraordinary_policy == 'fill_extr'):
                if (df2d(self.date).weekday() > 4):
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['EXTR_FESTIVO'])
                elif (i['from']%24 >= 22) or (i['from']%24 < 6):
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['EXTR_NOTTE'])
                else:
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['EXTR'])
                c_intervals += [i]

            elif total(c_intervals) < self._worked_time:
                if (i['from']%24 >= 22) or (i['from']%24 < 6):
                    if bonus == 'magp':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGP_NOTTE'])
                    elif bonus == 'magn':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGN_NOTTE'])
                    else:
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['OLAV'])
                elif (i['from']%24 >= 18):
                    if bonus == 'magp':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGP_SERA'])
                    elif bonus == 'magn':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGN_SERA'])
                    else:
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['OLAV'])
                else:
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['OLAV'])

               
                if total([i]) + total(c_intervals) > self._worked_time:
                    b = dict(i)
                    i['to'] = i['from'] + self._worked_time - total(c_intervals)
                    b['from'], b['type'] = i['to'], 'e'
                    _intervals.insert(0, b)

                c_intervals += [i]

        c_intervals = sorted(c_intervals, key = lambda x: (x['from']) )

        if (len(absences) == 1) & (self.get_nominal_pause() == 0) & (total(absences) <= 0.5):
            i = absences.pop(0)
            if (i['from'] >= c_intervals[0]['to']) & (i['to'] <= c_intervals[-1]['from']):
                i['type'] = 'w'
                i['code'] = self.env['hr.holidays.status'].browse(reasons['OLAV'])
                i = self.categ_interval(i) 
                c_intervals += i

        return sorted(c_intervals, key = lambda x: (x['from']) )


    def categ_interval(self, a):
        bonus = self.employee_id.payroll_bonus
        reasons = self._get_computed_reason_ids()
        _intervals = []
        intervals = []

        if not a.get('type', False):
            a['type'] = 'e' if a['code'].is_extra else 'w'
            
        if getattr(a['code'], 'calc', False) == False:
            return [a]
        else:
            if (a['from'] < 6) & (a['to'] >= 6):
                _intervals += [{'from': a['from'], 'to': 6, 'type':  a['type'], 'code': a['code']}]
                a['from'] = 6

            if (a['from'] < 18) & (a['to'] >= 18):    
                _intervals += [{'from': a['from'], 'to': 18, 'type':  a['type'], 'code': a['code']}]
                a['from'] = 18
        
            if (a['from'] < 22) & (a['to'] >= 22):
                _intervals += [{'from': a['from'], 'to': 22, 'type':  a['type'], 'code': a['code']}]
                a['from'] = 22
            
            if (a['from'] < 30) & (a['to'] >= 30):    
                _intervals += [{'from': a['from'], 'to': 30, 'type':  a['type'], 'code': a['code']}]
                a['from'] = 30

            if a['from'] != a['to']:
                _intervals += [a]

        for i in _intervals:
            if (i['type'] == 'e'):
                if (df2d(self.date).weekday() > 4):
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['EXTR_FESTIVO'])
                elif (i['from']%24 >= 22) or (i['from']%24 < 6):
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['EXTR_NOTTE'])
                else:
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['EXTR'])

            else:
                if (i['from']%24 >= 22) or (i['from']%24 < 6):
                    if bonus == 'magp':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGP_NOTTE'])
                    elif bonus == 'magn':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGN_NOTTE'])
                    else:
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['OLAV'])
                elif (i['from']%24 >= 18):
                    if bonus == 'magp':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGP_SERA'])
                    elif bonus == 'magn':
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['MAGN_SERA'])
                    else:
                        i['code'] = self.env['hr.holidays.status'].browse(reasons['OLAV'])
                else:
                    i['code'] = self.env['hr.holidays.status'].browse(reasons['OLAV'])
                    
            intervals += [i]
                
        return intervals

    def merge_intervals(self, intervals):
        i = 0
        while i < len(intervals):
            a = intervals[i]
            l = i+1
            while l < len(intervals):
                if (intervals[l]['code'] == a['code']) & (intervals[l]['from'] == a['to']):
                    a['to'] = intervals.pop(l)['to']
                else:
                    break
            i+=1

        return sorted(intervals, key = lambda x: (x['from']) )

    def compute_total_att(self):
        attendances_intrs = []
        date = df2d(self.date)
        nominals = [(int(x.dayofweek) - int(date.weekday()) + x.hour_from, int(x.dayofweek) - int(date.weekday()) + x.hour_to) for x in self._attendances_ids]

        for a in self.attendances_ids:
            
            time_from_o, time_to_o, time_from, time_to = False, False, False, False
            if a.check_in:
                cin = dt2dtn(dtf2dt(a.check_in), 'Europe/Rome', True)
                time_from_o, time_from = dtc2fwo(date, cin)
            if a.check_out:
                cot = dt2dtn(dtf2dt(a.check_out), 'Europe/Rome', True, False)
                time_to_o, time_to = dtc2fwo(date, cot)
            
            attendances_intrs += [{
                        'from': int(time_from_o)*24 + 0.25*(float(time_from)//0.25 + int(bool(float(time_from)%0.25))),
                        'to': max(int(time_from_o)*24 + 0.25*(float(time_from)//0.25), int(time_to_o)*24 + 0.25*(float(time_to)//0.25)),
                       }]
        try:
            if (((attendances_intrs[0]['from'] - nominals[0][0]) > 0)
                & ((attendances_intrs[0]['from'] - nominals[0][0]) <= 0.25)
                & ((attendances_intrs[-1]['to'] - nominals[-1][1]) >= 0.25)):
                attendances_intrs[0]['from'] -= 0.25
                attendances_intrs[-1]['to'] -= 0.25
        except IndexError:
            pass

        total = 0

        for intr in attendances_intrs:
            total += ( (intr['to']//0.5)*0.5 - ((intr['from']//0.5 + int(bool(float(intr['from'])%0.5)))*0.5))

        self.total_attended = total

    def load_intervals(self):
        intervals = []
        attendances_intrs = []
        date = df2d(self.date)
        self.holiday_ids = self.sudo().env['hr.holidays'].search( [ ('employee_id', '=', self.employee_id.ids[0]), ('date_from', '<=', self.work_to), ('date_to', '>=', self.work_from) ] )

        nominals = [(int(x.dayofweek) - int(date.weekday()) + x.hour_from, int(x.dayofweek) - int(date.weekday()) + x.hour_to) for x in self._attendances_ids]

        for a in self.attendances_ids:
            
            time_from_o, time_to_o, time_from, time_to = False, False, False, False
            if a.check_in:
                cin = dt2dtn(dtf2dt(a.check_in), 'Europe/Rome', True)
                time_from_o, time_from = dtc2fwo(date, cin)
            if a.check_out:
                cot = dt2dtn(dtf2dt(a.check_out), 'Europe/Rome', True, False)
                time_to_o, time_to = dtc2fwo(date, cot)
            
            attendances_intrs += [{
                        'from': int(time_from_o)*24 + 0.25*(float(time_from)//0.25 + int(bool(float(time_from)%0.25))),
                        'to': max(int(time_from_o)*24 + 0.25*(float(time_from)//0.25), int(time_to_o)*24 + 0.25*(float(time_to)//0.25)),
                        'code': self.env['hr.holidays.status'].browse(self._get_computed_reason_ids()['OLAV'])
                       }]
        try:
            if (((attendances_intrs[0]['from'] - nominals[0][0]) > 0)
                & ((attendances_intrs[0]['from'] - nominals[0][0]) <= 0.25)
                & ((attendances_intrs[-1]['to'] - nominals[-1][1]) >= 0.25)):
                attendances_intrs[0]['from'] -= 0.25
                attendances_intrs[-1]['to'] -= 0.25
        except IndexError:
            pass

        total = 0
        for intr in attendances_intrs:
            intervals += [{'from': (intr['from']//0.5 + int(bool(float(intr['from'])%0.5)) )*0.5,
                           'to':   (intr['to']//0.5)*0.5,
                           'code': intr['code']
                          }]
            total += ( (intr['to']//0.5)*0.5 - ((intr['from']//0.5 + int(bool(float(intr['from'])%0.5)))*0.5))

        self.total_attended = total

        #HOLIDAYS

        for h in self.holiday_ids:
            cin, cot = dt2dtn(dtf2dt(h.date_from), 'Europe/Rome', True), max( dt2dtn(dtf2dt(h.date_from), 'Europe/Rome', True), dt2dtn(dtf2dt(h.date_to), 'Europe/Rome', True, False) )

            time_from_o, time_from = dtc2fwo(date, cin)            
            time_to_o, time_to = dtc2fwo(date, cot)
            
            holiday = ( time_from_o*24 + time_from, time_to_o*24 + time_to )
            holidays = intrslice(holiday, nominals)

            for hol in holidays:

                time_from_o, time_from = hol[0]//24, hol[0] - 24*(hol[0]//24)
                time_to_o, time_to = hol[1]//24, hol[1] - 24*(hol[1]//24)

                intervals += [{
                            'from': int(time_from_o)*24 + 0.5*(float(time_from)//0.5 + int(bool(float(time_from)%0.5))),
                            'to': max(int(time_from_o)*24 + 0.5*(float(time_from)//0.5), int(time_to_o)*24 + 0.5*(float(time_to)//0.5)),
                            'code': h.holiday_status_id
                        }]     

        return intervals

    @api.multi
    def compute_payroll(self):
        for i in self:
            i.needed_action = 0
            i.anomaly_type = False

            date = df2d(i.date)
            intervals = [x for x in i.load_intervals() if (x['from'] != x['to'])]
            for a in intervals:
                if [x for x in intervals if ((x['from'] < a['to']) & (x['to'] > a['from']) & (x != a))]:
                    i.needed_action = 3
                    i.anomaly_type = 'is'
                    return

            #computa risultati

            steps = [(6, 0), (6, 0), (18, 0), (18, 0), (22, 0), (22, 0), (30, 0), (30, 0)]
            for x in i._attendances_ids:
                steps += [((int(x.dayofweek) - int(date.weekday()))*24 + x.hour_from, 0), ((int(x.dayofweek) - int(date.weekday()))*24 + x.hour_to, 0)]

            
            
            for x in intervals:
                steps += [(x['from'], x['code']), (x['to'], x['code'])]
            
            steps = sorted(steps, key = lambda x: (x[0], getattr(x[1], 'ids', [0])[0]))
            active, _active = bool(steps[0][1] != 0), bool(steps[0][1] == 0)
            intervals = []
            absences = []

            current_reason = 0

            for l in range(1, len(steps)):
                td = steps[l][0] - steps[l-1][0]
                current_reason = steps[l-1][1] if steps[l-1][1] != 0 else current_reason

                if (td < 0.5):
                    if steps[l][1]==0:
                        _active = not _active
                    elif steps[l][1]!=0:
                        active = not active
                    continue

                if (_active & active):
                    intervals += [{'to': steps[l][0],'from': steps[l-1][0], 'type': 'w', 'code': current_reason}]
                elif ((not _active) & active):
                    if not getattr(steps[l][1], 'isabsence', False):
                        intervals += [{'to': steps[l][0],'from': steps[l-1][0], 'type': 'e', 'code': current_reason}]
                elif (_active & (not active)):
                        absences += [{'to': steps[l][0],'from': steps[l-1][0], 'type': 'a', 'code': False}]

                if steps[l][1]==0:
                    _active = not _active
                elif steps[l][1]!=0:
                    active = not active

            intervals = i.apply_bonus(intervals, absences)

            def total(tuparray):
                total = 0
                for i in tuparray:
                    total += i['to'] - i['from']
                return total

            if (total(intervals)) < i._worked_time:
                intervals += absences

            i._calculate_day(intervals)
            
    @api.multi 
    def calculate_day(self):
        self._calculate_day()

    @api.multi
    def _calculate_day(self, intervals=False, soft=False):
        for i in self:
            
            if not soft:
                if intervals == False:
                    intervals = []
                    for x in i.intervals_ids:
                        intervals += i.categ_interval({'to': x.qtimet, 'from': x.qtimef, 'code':  x.reason})
            

                intervals = i.merge_intervals(intervals)

                i.intervals_ids.unlink()

                for intr in intervals:
                    time_from_o, time_from = intr['from']//24, intr['from'] - 24*(intr['from']//24)
                    time_to_o, time_to = intr['to']//24, intr['to'] - 24*(intr['to']//24)
                    i.sudo().env['rds.hr.working.unit.interval'].create({'time_from': time_from,
                                                                            'time_from_o': time_from_o,
                                                                            'time_to': time_to,
                                                                            'time_to_o': time_to_o,
                                                                            'working_unit_id': i.ids[0],
                                                                            'reason': False if not intr['code'] else intr['code'].ids[0]
                                                                        })


            i.anomaly_type, i.needed_action = False, 0

            if i.intervals_ids.filtered(lambda x: (x.time_from == False) or (x.time_to == False)):
                i.needed_action = 3
                i.anomaly_type = 'ia'
                return

            for a in i.intervals_ids:
                if i.intervals_ids.filtered(lambda x: (x.qtimef < a.qtimet) & (x.qtimet > a.qtimef) & (x.ids[0] != a.ids[0])):
                    i.needed_action = 3
                    i.anomaly_type = 'is'
                    return

            a = 0
            for l in i.intervals_ids.filtered(lambda x: bool(x.reason) != False):
                a += l.duration
            i.worked_time = a

            if (i.worked_time < i._worked_time) or bool(i.intervals_ids.filtered(lambda x: bool(x.reason) == False)):
                i.anomaly_type = 'ii'
                i.needed_action = 3
            elif (i.worked_time > i._worked_time) and bool(i.intervals_ids.filtered(lambda x: x.reason.is_absence != False)):
                i.anomaly_type = 'oca'
                i.needed_action = 3
            elif bool(i.intervals_ids.filtered(lambda x: (not x.reason.is_extra) and (not x.reason.is_absence)).get_total() > i._worked_time):
                i.anomaly_type = 'oho'
                i.needed_action = 3
            elif (i.total_attended > i.worked_time) and bool(i.intervals_ids.filtered(lambda x: x.reason.is_extra == True)):
                i.anomaly_type = 'spp'
                i.needed_action = 1
            elif i.total_attended > i.worked_time:
                i.anomaly_type = 'ie'
                i.needed_action = 2
            elif i.worked_time > i._worked_time:
                i.anomaly_type = 'sp'
                i.needed_action = 1

            i.get_gis_payroll()

    @api.multi
    def reload_day(self):
        for i in self:
            i.compute_payroll()

        
    @api.model
    def create_working_units(self):
        for e in self.env['hr.employee'].search([]):
            try:
                if not self.env['rds.hr.working.unit'].search([('date', '=', fields.Date.today()), ('employee_id', '=', e.ids[0])]):
                    self.env['rds.hr.working.unit'].create({'employee_id': e.ids[0], 'extraordinary_policy': e.extraordinary_policy, 'working_schedule': e.resource_calendar_id.ids[0], 'date': fields.Date.today()})
            except Exception:
                continue

    @api.model
    def pull_work_data(self):
        self.env['rds.hr.working.unit'].search([('date', '>=', (datetime.now() - timedelta(1)).strftime(DEFAULT_SERVER_DATE_FORMAT) )]).reload_day()


    @api.model                                                          
    def MASS_UPDATE(self, eid, eid2, soft=False):                                             # DISABILITARE QUESTO METODO!!!
        y = [x for x in range(eid, eid2)]
        if soft:
            emps = self.env['rds.hr.working.unit'].search([('employee_id', 'in', y)])
            for i in emps:
                i.compute_total_att()
                i._calculate_day()
        else:
            self.env['rds.hr.working.unit'].search([('employee_id', 'in', y)]).reload_day()


    @api.model
    def fix_wus(self, day, day2=False, edom=[]):
        date = datetime(day[0], day[1], day[2])

        if day2:
            date2 = datetime(day2[0], day2[1], day2[2])
            while date != date2:
                for e in self.env['hr.employee'].search(edom):
                    try:
                        if not self.env['rds.hr.working.unit'].search([('date', '=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)), ('employee_id', '=', e.ids[0])]):
                            self.env['rds.hr.working.unit'].create({'employee_id': e.ids[0], 'extraordinary_policy': e.extraordinary_policy, 'working_schedule': e.resource_calendar_id.ids[0], 'date': date.strftime(DEFAULT_SERVER_DATE_FORMAT)})
                    except Exception:
                        continue
                date += timedelta(1)

        for e in self.env['hr.employee'].search(edom):
            try:
                if not self.env['rds.hr.working.unit'].search([('date', '=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)), ('employee_id', '=', e.ids[0])]):
                    self.env['rds.hr.working.unit'].create({'employee_id': e.ids[0], 'extraordinary_policy': e.extraordinary_policy, 'working_schedule': e.resource_calendar_id.ids[0], 'date': date.strftime(DEFAULT_SERVER_DATE_FORMAT)})
            except Exception:
                continue
    
    @api.model
    def fix_all_30_08(self):
        ferie = self.env['hr.holidays.status'].browse(65)
        records = self.env['rds.hr.working.unit'].search([('date', '>=', '2018-08-13'), ('date', '<=', '2018-08-31')])
        for i in records:
            if i.intervals_ids == False:
                i.reload_day()

            for x in i.intervals_ids:
                if x.reason == False:
                    x.reason = ferie

            
    @api.multi
    def get_all_intervals(self):
        return self.env['rds.hr.working.unit.interval'].search([('working_unit_id', 'in', self.ids)])


class ResourceCalendarAttendance(models.Model):
    _inherit = ['resource.calendar.attendance']


    def get_pause_duration(self, other):
        self_from, self_to = int(self.dayofweek)*24 + self.hour_from, int(self.dayofweek)*24 + self.hour_to
        other_from, other_to = int(other.dayofweek)*24 + other.hour_from, int(other.dayofweek)*24 + other.hour_to
        if self_to <= other_from:
            return timedelta((other_from - self_to)/24)
        else:
            other_from += 24*7
            return timedelta((other_from - self_to)/24)

    def get_check_in_deviation(self, time, sign=False):
        t = datetime(time.year, time.month, time.day, 0, 0) + float_to_timedelta(self.hour_from)

        _time = pytz.timezone('Europe/Rome').localize(t)

        if sign:
            return (time - _time)

        return ((time - _time) if time > _time else (_time - time))
    
    def get_check_out_deviation(self, time, sign=False):
        t = datetime(time.year, time.month, time.day,  0, 0) + float_to_timedelta(self.hour_to)

        _time = pytz.timezone('Europe/Rome').localize(t)

        if sign:
            return (time - _time)


        return ((time - _time) if time > _time else (_time - time))
    
    def _get_previous_connected(self):
        a = self.calendar_id.attendance_ids.filtered(lambda a: ( (a.get_pause_duration(self) <= PAUSE_TOLLERANCE) 
                                                               & (a.ids[0] != self.ids[0])
                                                               ))
        return False if (not a) else a[0]

    def _get_next_connected(self):
        a = self.calendar_id.attendance_ids.filtered(lambda a: ( (self.get_pause_duration(a) <= PAUSE_TOLLERANCE) 
                                                               & (a.ids[0] != self.ids[0])
                                                               ))
        return False if (not a) else a[0]

    def get_attendances_chain(self):
        a = self
        records = self.env['resource.calendar.attendance']
        while a:
            records += a[0]
            a = a[0].calendar_id.attendance_ids.filtered(lambda n: ( ((int(n.dayofweek)*24.0 + n.hour_from) >= (int(a.dayofweek)*24.0 + a.hour_to) ) & (timedelta(((int(n.dayofweek)*24.0 + n.hour_from) - (int(a.dayofweek)*24.0 + a.hour_to))/24) <= PAUSE_TOLLERANCE) & (n.ids[0] != a.ids[0]))).sorted(key=lambda n: (int(n.dayofweek)*24.0 + n.hour_from))
        return records

    def get_first_checkin(self, date):
        return d2dt(df2d(date), 'Europe/Rome').astimezone(pytz.utc) - PAUSE_TOLLERANCE + float_to_timedelta(self.hour_from)

    def get_last_checkin(self, date, other=False):
        return d2dt(df2d(date),'Europe/Rome').astimezone(pytz.utc) + PAUSE_TOLLERANCE + float_to_timedelta(self.hour_to) + timedelta(int(self.dayofweek) - int(other.dayofweek)) 

class HrAttendance(models.Model):
    _inherit = ['hr.attendance']

    working_unit_id = fields.Many2one('rds.hr.working.unit', string="Unità Lavorativa", ondelete='cascade')

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        pass

    def get_localized_cin(self, day=False):
        tf = "%d" if day else "%H:%M"
        dt = pytz.utc.localize(dtf2dt(self.check_in)).astimezone(pytz.timezone("Europe/Rome")).strftime(tf)
        return dt

    def get_localized_cot(self, day=False):
        tf = "%d" if day else "%H:%M"
        dt = pytz.utc.localize(dtf2dt(self.check_out)).astimezone(pytz.timezone("Europe/Rome")).strftime(tf)
        return dt

    @api.model
    def create(self, vals):
        if not ('working_unit_id' in vals):
            prev = self.env['hr.attendance'].search([('employee_id', '=', vals['employee_id']), 
                                                    ('check_out', '>=', dt2dtf(dtf2dt(vals['check_in']) - PAUSE_TOLLERANCE) ), 
                                                    ('check_in', '<', vals['check_in'])])
            if prev:
                first = prev[0].get_first_in_chain()
                try:
                    wu = first.working_unit_id
                except AttributeError:
                    wu = first[0].working_unit_id
            else:
                wu = self.sudo().env['rds.hr.working.unit'].search([('employee_id', '=', vals['employee_id'])], limit=1)
            if wu:
                vals['working_unit_id'] = wu.ids[0]
            att = super(HrAttendance, self).create(vals)
            wu.reload_day()
        else:
            att = super(HrAttendance, self).create(vals)
            
        return att

    @api.multi
    def write(self, vals):
        for i in self:
            super(HrAttendance, self).write(vals)
            i.working_unit_id.sudo().reload_day()

    
    @api.multi
    def unlink(self):
        wu = self.sudo().env['rds.hr.working.unit']
        for i in self:
            wu += i.working_unit_id
        super(HrAttendance, self).unlink()

        wu.reload_day()

    def get_first_in_chain(self):
        prev = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.ids[0]),
                                                 ('check_out', '>=', dt2dtf(dtf2dt(self.check_in) - PAUSE_TOLLERANCE) ),
                                                 ('check_in', '<', self.check_in)])
        if prev:
            return prev[0].get_first_in_chain()
        else:
            return self

    @api.multi
    def _close_open_attendances(self):
        for i in self:
            delta = datetime.now() - dtf2dt(i.check_in)
            if delta > timedelta(0.5) and (not i.check_out):
                    i.check_out = i.check_in

    @api.model
    def close_open_attendances(self):
        self.env['hr.attendance'].search([('check_out', '=', False)])._close_open_attendances()
    

    def get_markings_chain(self):
        a = self
        records = self.env['hr.attendance']
        while a:
            records += a[0]
            a = a[0].employee_id.attendance_ids.filtered(lambda n: ( (dtf2dt(n.check_in) > dtf2dt(a.check_out)) & ((dtf2dt(n.check_in) - dtf2dt(a.check_out)) <= PAUSE_TOLLERANCE) & (n.ids[0] != a.ids[0]))).sorted(key=lambda n: n.check_in)
        return records

    @api.model
    def mass_reset_wu(self, n):
        atts = self.search([('id', '>=', n)])
        for i in atts:
            cin = dt2dtn(dtf2dt(i.check_in), 'Europe/Rome', True)
            if cin.hour <= 5:
                date = cin.date() + timedelta(-1)
            else:
                date = cin.date()
            
            wu = self.env['rds.hr.working.unit'].search([('date', '=', date.strftime(DEFAULT_SERVER_DATE_FORMAT)), ('employee_id', '=', i.employee_id.id)])
            if wu:
                i.working_unit_id = wu[0]


class HrHoliday(models.Model):
    _inherit = ['hr.holidays']
    _order = "date_from"
    
    working_unit_ids = fields.Many2many('rds.hr.working.unit', 'working_unit_holidays_rel', string="Unità Lavorativa")
    longterm = fields.Boolean('Lungo Termine', compute="_is_long_term", readonly=True)

    @api.model
    def create(self, vals):
        if not 'working_unit_ids' in vals:
            wu = self.sudo().env['rds.hr.working.unit'].search([('employee_id', '=', vals['employee_id']), ('work_to', '>=', vals['date_from']), ('work_from', '<=', vals['date_to'])])
            vals['working_unit_ids'] = [(4, x.ids[0]) for x in wu]
            new = super(HrHoliday, self).create(vals)
            wu.reload_day()
            return new
        else: 
            return super(HrHoliday, self).create(vals)


    @api.multi
    def write(self, values):
        for i in self:
            values['working_unit_ids'] = [(4, x.ids[0]) for x in self.sudo().env['rds.hr.working.unit'].search([('employee_id', '=', self.employee_id.ids[0]), ('work_to', '>=', self.date_from), ('work_from', '<=', self.date_to)])]
            super(HrHoliday, self).write(values)
            i.working_unit_ids.reload_day()
    
    @api.multi
    def unlink(self):
        wu = self.sudo().env['rds.hr.working.unit']
        for i in self:
            wu += i.working_unit_ids
        super(HrHoliday, self).unlink()

        wu.reload_day()

    @api.depends('date_to', 'date_from')
    def _is_long_term(self):
        for i in self:
            longterm = False
            if bool(i.date_to) & bool(i.date_from):
                date_from = dtf2dt(i.date_from)
                date_to = dtf2dt(i.date_to)
                if date_to - date_from >= timedelta(18/24):
                    longterm = True
            i.longterm = longterm

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            return math.ceil(employee.get_work_days_data(from_dt, to_dt)['hours']/0.25)*0.25

        time_delta = to_dt - from_dt
        return math.ceil((time_delta.days*86400 + float(time_delta.seconds) / 3600)/0.25)*0.25

    @api.onchange('date_from')
    def _onchange_date_from(self):
        """ If there are no date set for date_to, automatically set one 8 hours later than
            the date_from. Also update the number_of_days.
        """
        if bool(self.date_to) & bool(self.date_from):
            date_to = dt2dtf(dt2dtn(dtf2dt(self.date_to), ceil=True))
            date_from = dt2dtf(dt2dtn(dtf2dt(self.date_from), ceil=True))
            self.number_of_days_temp = self._get_number_of_days(date_from, date_to, self.employee_id.id)
        elif self.date_from:
            date_from = dt2dtf(dt2dtn(dtf2dt(self.date_from), ceil=True))
            self.date_to = self.date_from
            self.z = 0

    @api.onchange('date_to')
    def _onchange_date_to(self):
        """ Update the number_of_days. """
        if bool(self.date_to) & bool(self.date_from):
            date_to = dt2dtf(dt2dtn(dtf2dt(self.date_to), ceil=True))
            date_from = dt2dtf(dt2dtn(dtf2dt(self.date_from), ceil=True))
            if (date_from <= date_to):
                self.number_of_days_temp = self._get_number_of_days(date_from, date_to, self.employee_id.id)
            else:
                self.number_of_days_temp = 0


class HrHolidayType(models.Model):
    _inherit = ['hr.holidays.status']
    
    payroll_code = fields.Char(string="Codice Evento", size=6, default="*OLAV")

    calc = fields.Boolean("Calcola come Ore Lavorate")

    is_extra = fields.Boolean(string="Causale di Straordinario")
    is_absence = fields.Boolean(string="Causale di Assenza")

    system = fields.Boolean(string="Causale di Sistema")

    justification_category = fields.Selection(selection=[
        ('wh', 'Ore Ordinarie'),
        ('extra', 'Straordinari'),
        ('pleave', 'Permessi pagati'),
        ('inps', 'Assenze INPS'),
        ('unpaid', 'Non Pagato')
    ], default="wh", store=True, string="Tipo Giustificativo")

    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for holiday in self:
            domain = [
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('type', '=', holiday.type),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_('You can not have 2 leaves that overlaps on same day!'))



