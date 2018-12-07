# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models, _
from odoo.addons.resource.models.resource import Intervals
import datetime as dt
import pytz, logging
from pytz import utc
from collections import namedtuple
from math import sqrt

_logger = logging.getLogger()


### Queries



reason_view = """

-- View Definition:

SELECT ROW_NUMBER() OVER (ORDER BY day_id) AS id, * FROM (

        SELECT one.id AS day_id, one.workbook_id, one.date, tp.att_type, one.reason_1 AS reason_id, qty_1 AS qty
            FROM hr_attendance_day one 
            LEFT JOIN hr_attendance_type tp ON tp.id = one.reason_1
            WHERE one.reason_1 IS NOT NULL
        UNION ALL

        SELECT two.id AS day_id, two.workbook_id, two.date, tp.att_type, two.reason_2 AS reason_id, two.qty_2 AS qty
            FROM hr_attendance_day two
            LEFT JOIN hr_attendance_type tp ON tp.id = two.reason_2
            WHERE two.reason_2 IS NOT NULL
        UNION ALL
        
        SELECT three.id AS day_id, three.workbook_id, three.date, tp.att_type, three.reason_3 AS reason_id, three.qty_3 AS qty
            FROM hr_attendance_day three 
            LEFT JOIN hr_attendance_type tp ON tp.id = three.reason_3
            WHERE three.reason_3 IS NOT NULL
        UNION ALL

        SELECT four.id AS day_id, four.workbook_id, four.date, tp.att_type, four.reason_4 AS reason_id, four.qty_4 AS qty
        FROM hr_attendance_day four 
        LEFT JOIN hr_attendance_type tp ON tp.id = four.reason_4
        WHERE four.reason_4 IS NOT NULL
        
    ) x
"""

def normalize(dtime, mode="UP"):
    if mode=="UP":
        if dtime.minute >= 30:
            dtime = (dtime + dt.timedelta(0, 1800)).replace(minute=0, second=0, microsecond=0)
        else:
            dtime = dtime.replace(minute=30, second=0, microsecond=0)
    if mode=="DOWN":
        if dtime.minute < 30:
            dtime = dtime.replace(minute=0, second=0, microsecond=0)
        else:
            dtime = dtime.replace(minute=30, second=0, microsecond=0)
        
    return dtime

def normalize_ranges(ranges):
    for i in range(0, len(ranges)):
        ranges[i] = ranges[i]._replace(start=normalize(ranges[i].start, 'UP'), end=normalize(ranges[i].end, 'DOWN'))
    return ranges

def overlaps(a, b, init=0):
    return max(min(a[1], b[1]) - max(a[0], b[0]), init)

def total_overlaps(a, b, init=0):
    out = init

    for i in a:
        for j in b:
            out += overlaps(i, j, init)

    return out

class HrAttendanceBook(models.Model):
    _name = 'hr.attendance.book'
    _description = "Attendance Book"
    _order = "year, month, issues DESC, employee_id"

    def _compute_totals(self):
        for book in self:
            query = "SELECT att_type, sum(qty) FROM (%s) t GROUP BY att_type;" % (reason_view + " WHERE workbook_id=%s" % book.id)
            self._cr.execute(query)
            result = self._cr.fetchall()

            for i in result:
                if i[0] == 'work':
                    book.total_worked = i[1]
                if i[0] == 'extra':
                    book.total_extra = i[1]
                if i[0] == 'hol':
                    book.total_holiday = i[1]
                if i[0] == 'absn':
                    book.total_absence = i[1]

            book.grand_total_e = sum(book.day_ids.mapped(lambda x: x.total_e))
            book.grand_total = sum(map(lambda x: x[1], result))                

    def _get_days(self):
        for book in self:
            book.date_start = dt.date(year=int(book.year), month=book.month, day=1)
            book.date_end = (dt.date(year=int(book.year), month=book.month, day=1) + dt.timedelta(32)).replace(day=1) - dt.timedelta(1)

    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', 'Dipendente')

    date_start = fields.Date("First of Month", compute=_get_days)
    date_end = fields.Date("Last of Month", compute=_get_days)

    grand_total = fields.Float("Grand Total", compute=_compute_totals)
    grand_total_e = fields.Float("Grand Total Excepted", compute=_compute_totals)

    total_worked = fields.Float("Total Worked", compute=_compute_totals)
    total_extra = fields.Float("Total Extra", compute=_compute_totals)
    total_holiday = fields.Float("Total Holiday", compute=_compute_totals)
    total_absence = fields.Float("Total Absence", compute=_compute_totals)

    year = fields.Char("Year", readonly=True)
    month = fields.Selection([
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December')
        ], required=True, readonly=True)

    day_ids = fields.One2many('hr.attendance.day', 'workbook_id', string="Days")

    @api.depends('day_ids.issues')
    def _issues(self):
        for i in self:
            if any(i.day_ids.mapped(lambda x: x.issues)):
                i.issues = True

    issues = fields.Boolean('Issues', compute=_issues, store=True)

    @api.model
    def generate_books(self, frm=dt.date.today().replace(day=1)):
        year, month = str(frm.year), frm.month

        _to = frm + dt.timedelta(32)
        to = _to - dt.timedelta(days=_to.day)
        del _to
        
        for emp in self.env['hr.employee'].search([]):
            if self.search([('employee_id', '=', emp.id), ('year', '=', year), ('month', '=', month)]):
                continue
            self.sudo().create({
                'employee_id': emp.id,
                'year': year,
                'month': month,
                'name': _("Attendance Book {}/{} for {}").format(year, month, emp.name),
                'day_ids': [(0, 0, {'date': dt.date(year=int(year), month=month, day=day), 'resource_calendar_id': emp.resource_calendar_id.id, 'structure_id': emp.structure_id.id}) for day in range(frm.day, to.day+1)]
            })

    @api.multi
    def load_all(self):
        for book in self:
            book.day_ids.load()

    @api.multi
    def action_view_days(self):
        return {
            'name': _("Attendance Days"),
            'res_model': 'hr.attendance.day',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('workbook_id', '=', self.id)],
        }


    @api.multi
    def _get_attendances(self):
        for i in self:
            i.attendance_ids = i.day_ids.mapped(lambda x: x.attendance_ids)

    @api.multi
    def _get_leaves(self):
        for i in self:
            i.leave_ids = i.day_ids.mapped(lambda x: x.leave_ids)

    attendance_ids = fields.Many2many('hr.attendance', compute=_get_attendances)
    leave_ids = fields.Many2many('hr.leave', compute=_get_leaves)


class HrAttendanceDay(models.Model):
    _name = 'hr.attendance.day'
    _description = "Attendance Day"

    def cron_load(self, force=False):
        to_load = self.search([('date', '<', fields.Date.to_string(fields.Date.today()))] + ([('cron_loaded', '=', False)] if force else []))
        to_load.load()

    def _get_day_info(self):
        for i in self:
            i.day = i.date.day
            i.dayofweek = i.date.weekday()
            i.passed = i.date < dt.date.today()

    def _refresh_day(self, mode='hard'):
        self.ensure_one()
        if mode == 'hard':
            self.resource_calendar_id = self.workbook_id.employee_id.resource_calendar_id or self.env['res.company']._company_default_get().resource_calendar_id
            start_dt, end_dt = self._get_ranges()
            self.total_e = self.resource_calendar_id.get_work_hours_count(start_dt, end_dt, False)
            self.structure_id = self.employee_id.structure_id
            return start_dt, end_dt

    @api.multi
    def _get_attendances(self):
        for i in self:
            if not i.date:
                return False

            start_dt, end_dt = i._get_ranges(True)
            ts = fields.Datetime.to_string
            i.attendance_ids = self.sudo().env['hr.attendance'].search([
                '&', '&',
                ('employee_id', '=', i.employee_id.id),
                ('check_in', '<=', ts(end_dt)),
                '|',
                ('check_out', '>=', ts(start_dt)), ('check_out', '=', False), 
            ]) or False

    @api.multi
    def _get_leaves(self):
        for i in self:
            if not i.date:
                return False
                
            start_dt, end_dt = i._get_ranges(True)
            ts = fields.Datetime.to_string
            i.leave_ids = self.sudo().env['hr.leave'].search([
                '&', '&', '&',
                ('state', '=', 'validate'),
                ('employee_id', '=', i.employee_id.id),
                ('date_from', '<=', ts(end_dt)),
                ('date_to', '>=', ts(start_dt))
            ]) or False

    @api.multi
    def load(self):
        for i in self:
            start_dt, end_dt = i._refresh_day()

            tz = pytz.timezone(i.resource_calendar_id.tz)
            total_e = i.total_e
            total_attended = sum(i.attendance_ids.mapped(lambda x: x.worked_hours))

            absence_index = 0 if total_e == 0 else max((total_e - total_attended) / total_e, 0)
            unadherence_index = 0

            _intervals = i.resource_calendar_id._attendance_intervals(start_dt, end_dt)

            
            # Range Computation

            Range = namedtuple('Range', ['start', 'end'])
            _att = list()
            att = list()

            for a in _intervals:
                _att.append(Range(a[0], a[1]))

            reasons = dict()
            allocated = 0

            if bool(i.attendance_ids) and (sum(i.attendance_ids.mapped(lambda x: x.worked_hours)) >= 0.25):
                for a in i.attendance_ids:
                    if not a.check_out:
                        continue

                    att.append(Range(max(utc.localize(a.check_in).astimezone(tz), start_dt), min(utc.localize(a.check_out).astimezone(tz), end_dt)))

                overlap = total_overlaps(_att, att, dt.timedelta(0)).total_seconds()/3600

                unadherence_index = 0 if total_e == 0 else sqrt(
                    (1 - (overlap/total_e))**2 + ((total_attended - overlap)/total_attended)**2
                )/2

                if att and _att:
                    delta = (att[0].start - _att[0].start).total_seconds()
                    if delta > 0:
                        if delta <= 900:
                            i.short_lateness = True
                        elif delta <= 1800:
                            i.long_lateness = True
                    
                    if i.short_lateness and (total_attended >= total_e):  # We grace short lateness, but we keep track of it.
                        delta = (att[-1].end - _att[-1].end).total_seconds() 
                        if delta >= 900:
                            att[0].start = att[0]._replace(start=att[0].start + dt.timedelta(0, 900))
                            att[-1].start = att[-1]._replace(start=att[-1].end - dt.timedelta(0, 900))

                att = normalize_ranges(att)

                if i.structure_id:
                    lines = [
                            (
                            k.reason_id.id,
                            k.reason_extra_id.id,
                            Range(start_dt + dt.timedelta(k.time_start/24), start_dt + dt.timedelta(k.time_end/24))
                            ) 
                            for k in i.structure_id.lines]

                    for line in lines:
                        to_alloc = total_overlaps([line[2]], att, dt.timedelta(0)).total_seconds() / 3600

                        if to_alloc + allocated > total_e:
                            reasons[line[0]] = reasons.get(line[0], 0) + total_e - allocated
                            reasons[line[1]] = reasons.get(line[1], 0) + to_alloc - total_e + allocated
                            allocated = total_e
                        else:
                            reasons[line[0]] = reasons.get(line[0], 0) + to_alloc
                            allocated = to_alloc + allocated

            if i.leave_ids.filtered(lambda x: bool(x.holiday_status_id.attendance_type)):
                lines = [
                    (
                        l.holiday_status_id.attendance_type,
                        Range(l.date_start, l.date_end)
                    )
                for l in i.leave_ids]

                for line in lines:
                    to_alloc = total_overlaps([line[1]], _att, dt.timedelta(0)).total_seconds() / 3600

                    if to_alloc + allocated > total_e:
                        reasons[line[0]] = reasons.get(line[0], 0) + total_e - allocated
                        break
                    else:
                        reasons[line[0]] = reasons.get(line[0], 0) + to_alloc
                        allocated = to_alloc + allocated


            #This cleans the day and reloads
            vals = dict()
            for z in range(1,5):
                vals['reason_{}'.format(z)] = False
                vals['qty_{}'.format(z)] = 0

            z = 0

            for key in reasons.keys():
                if reasons[key] <= 0.25:
                    continue

                z += 1
                if z > 4:
                    break

                vals['reason_{}'.format(z)] = key
                vals['qty_{}'.format(z)] = reasons[key]
            
            if vals:
                i.write({'cron_loaded': True, 'absence_index': absence_index, 'unadherence_index': unadherence_index, **vals})
                
    def _get_ranges(self, unaware=False):
        self.ensure_one()
        tz = pytz.timezone(self.resource_calendar_id.tz or 'UTC')
        start_dt = tz.localize(dt.datetime.combine(self.date, dt.time()))
        end_dt = tz.localize(dt.datetime.combine(self.date, dt.time())) + dt.timedelta(1)

        if unaware == True:
            start_dt = start_dt.astimezone(utc).replace(tzinfo=None)
            end_dt = end_dt.astimezone(utc).replace(tzinfo=None)
        
        return start_dt, end_dt


    workbook_id = fields.Many2one('hr.attendance.book', 'Book')
    employee_id = fields.Many2one('hr.employee', 'Employee', related="workbook_id.employee_id")
    structure_id = fields.Many2one('hr.attendance.structure')
    
    date = fields.Date("Date", readonly=True)

    day = fields.Integer("Day", compute=_get_day_info)
    dayofweek = fields.Selection([
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
        ], 'Day of Week', compute=_get_day_info)

    def _dow_char(self):
        for i in self:
            i._dayofweek_letter = _('MTWTFSS -- First six characters should be localized initals of weekdays.')[i.dayofweek]
            
    _dayofweek_letter = fields.Char(compute=_dow_char)

    passed = fields.Boolean("Passed", compute=_get_day_info)
    cron_loaded = fields.Boolean("Loaded by Cron")

    reason_1 = fields.Many2one('hr.attendance.type', "Reason 1")
    reason_2 = fields.Many2one('hr.attendance.type', "Reason 2")
    reason_3 = fields.Many2one('hr.attendance.type', "Reason 3")
    reason_4 = fields.Many2one('hr.attendance.type', "Reason 4")

    qty_1 = fields.Float("Qty 1")
    qty_2 = fields.Float("Qty 2")
    qty_3 = fields.Float("Qty 3")
    qty_4 = fields.Float("Qty 4")

    total_e = fields.Float("Total Excepted", readonly=True)

    short_lateness = fields.Boolean("Short Lateness", readonly=True)
    long_lateness = fields.Boolean("Long Lateness", readonly=True)

    unadherence_index = fields.Float("Unadherence Index", readonly=True, oldname="adherence_index")
    absence_index = fields.Float("Absence Index", readonly=True)

    attendance_ids = fields.Many2many('hr.attendance', compute=_get_attendances)
    leave_ids = fields.Many2many('hr.leave', compute=_get_leaves)

    @api.depends('reason_1', 'qty_1',
                 'reason_2', 'qty_2',
                 'reason_3', 'qty_3',
                 'reason_4', 'qty_4',
                 'total_e')
    def _check_reasons_qty(self):
        def getrow(att, _in=[]):
            for k in range(1,5):
                if getattr(att, 'qty_{}'.format(k), 0) == 0:
                    continue

                if getattr(
                        getattr(att, 'reason_{}'.format(k), False),
                        'att_type',
                        False) in _in:
                        return True
            return False

        for i in self:
            issues = False
            total = i.qty_1 + i.qty_2 + i.qty_3 + i.qty_4
            has_extra = False
            work = False

            if i.passed:
                work = getrow(i, ['work'])
                has_extra = getrow(i, ['extra'])
                if (total < i.total_e) or (has_extra and getrow(i, ['absn', 'hol'])):
                    issues = True

            if work and not i.attendance_ids:
                i.bad_markings = True

            i.issues = issues
            i.has_extra = has_extra
            i.total = total

    bad_markings = fields.Boolean("Bad Markings", compute=_check_reasons_qty, store=True, readonly=True)
    total = fields.Float("Total", compute=_check_reasons_qty, store=True)
    issues = fields.Boolean('Issues', compute=_check_reasons_qty, store=True)
    has_extra = fields.Boolean('Has Extra', compute=_check_reasons_qty, store=True)
    pay_extra = fields.Boolean('Pay Extras')
    
    resource_calendar_id = fields.Many2one('resource.calendar', "Working Schedule", oldname="schedule")

    @api.multi
    def name_get(self):
        return [(record.id, "{}'s attendance on {}".format(record.employee_id.name, record.date)) for record in self]

    @api.multi
    def write(self, vals):
        reasons = {}
        for i in range(1,5):
            reason = vals.get(
                            'reason_{}'.format(i), 
                            getattr(
                                getattr(self, 'reason_{}'.format(i), False), 
                                'id', 
                                False)
                                )
            qty = vals.get(
                            'qty_{}'.format(i), 
                            getattr(self, 'reason_{}'.format(i), False), 
                                )

            if bool(reason) and (qty >= 0):
                reasons[reason] = reasons.get(reason, 0) + qty
        
        reasons = list(reasons.items())

        for i in range(1,5):
            reason = reasons.pop()
            vals['reason_{}'.format(i)] = reason[0]
            vals['qty_{}'.format(i)] = reason[1]

        super(HrAttendanceDay, self).write(vals)


class HrAttendanceType(models.Model):
    _name = 'hr.attendance.type'
    _description = "Attendance Type"

    name = fields.Char("Description", required=True)
    code = fields.Char("Code", limit=5, required=True)

    att_type = fields.Selection([
        ('work', 'Attendance'),
        ('extra', 'Extra Attendance'),
        ('hol', 'Holiday'),
        ('absn', 'Absence')
        ], 'Attendance Type', required=True, index=True, default='absn')


class HrAttendanceStructure(models.Model):
    _name = 'hr.attendance.structure'
    _description = "Attendance Structures"

    name = fields.Char("Description", required=True)
    code = fields.Char("Code", required=True, limit=8)

    lines = fields.One2many('hr.attendance.structure.line', 'structure_id', "Structure Lines")


class HrAttendanceStructureLine(models.Model):
    _name = 'hr.attendance.structure.line'
    _description = "Attendance Structure Lines"

    structure_id = fields.Many2one('hr.attendance.structure', 'Structure', required=True, ondelete='cascade')

    time_start = fields.Float("Start", required=True)
    time_end = fields.Float("End", required=True)

    reason_id = fields.Many2one('hr.attendance.type', "Applied Reason", required=True, domain=[('att_type', '=', 'work')])
    reason_extra_id = fields.Many2one('hr.attendance.type', "Applied Reason for Extras", domain=[('att_type', '=', 'extra')], required=True)


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    attendance_type = fields.Many2one('hr.attendance.type', "Applied Reason", domain=[('att_type', '=', ['absn', 'hol'])])