# Intended for sole use by RDS Moulding Technology SpA. See README file.

from odoo import api, fields, models, _
import datetime as dt

class HrAttendanceBook(models.Model):
    _name = 'hr.attendance.book'
    _description = "Attendance Book"

    name = fields.Char('Name')
    employee_id = fields.Many2one('hr.employee', 'Dipendente')

    year = fields.Integer("Year", readonly=True)
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

    day_ids = fields.One2many('hr.attendance.day', 'worksheet_id', string="Days")

    def generate_books(self, frm=dt.date.today().replace(day=1)):
        year, month = frm.year, frm.month

        _to = frm + dt.timedelta(32)
        to = _to - dt.timedelta(days=_to.day)
        del _to
        
        for emp in self.env['hr.employee'].search([]):
            if self.search([('employee_id', '=', emp.id), ('year', '=', year), ('month', '=', month)]):
                continue
            self.create({
                'employee_id': emp.id,
                'year': year,
                'month': month,
                'name': _("Attendance Book {}/{} for {}").format(year, month, emp.name),
                'day_ids': [(0, 0, {'date': dt.date(year=year, month=month, day=day)}) for day in range(frm.day, to.day+1)]
            })


class HrAttendanceDay(models.Model):
    _name = 'hr.attendance.day'
    _description = "Attendance Day"

    def _get_day(self):
        for i in self:
            i.day = i.date.day
            i.dayofweek = i.date.weekday()
            i.passed = i.date <= dt.date.today()

    def _get_late_index(self):
        pass
    
    def _get_absence_index(self):
        pass

    @api.multi
    def _get_intervals(self):
        for i in self:
            intr_1 = i.interval_ids.filtered(lambda x: x.sequence == 1)
            if intr_1:
                intr_1 = intr_1[0]
                i.reason_1, i.qty_1 = intr_1.reason.id, intr_1.qty

            intr_2 = i.interval_ids.filtered(lambda x: x.sequence == 2)
            if intr_2:
                intr_2 = intr_2[0]
                i.reason_2, i.qty_2 = intr_2.reason.id, intr_2.qty

            intr_3 = i.interval_ids.filtered(lambda x: x.sequence == 3)
            if intr_3:
                intr_3 = intr_3[0]
                i.reason_3, i.qty_3 = intr_3.reason.id, intr_3.qty

            intr_4 = i.interval_ids.filtered(lambda x: x.sequence == 4)
            if intr_4:
                intr_4 = intr_4[0]
                i.reason_4, i.qty_4 = intr_4.reason.id, intr_4.qty

    def _set_intervals(self):
        self.ensure_one()
        intr = list()

        if self.reason_1:
            intr.append((0, 0, {'date': self.date, 'day_id': self.id, 'sequence': 1, 'reason_id': self.reason_1.id, 'qty': self.qty_1}))
        if self.reason_2:
            intr.append((0, 0, {'date': self.date, 'day_id': self.id, 'sequence': 2, 'reason_id': self.reason_2.id, 'qty': self.qty_2}))
        if self.reason_3:
            intr.append((0, 0, {'date': self.date, 'day_id': self.id, 'sequence': 3, 'reason_id': self.reason_3.id, 'qty': self.qty_3}))
        if self.reason_4:
            intr.append((0, 0, {'date': self.date, 'day_id': self.id, 'sequence': 4, 'reason_id': self.reason_4.id, 'qty': self.qty_4}))

        self.update({'interval_ids': [5]})
        self.update({'interval_ids': intr})
        

    worksheet_id = fields.Many2one('hr.attendance.book', 'Book')

    date = fields.Date("Date", readonly=True)

    day = fields.Integer("Day", compute=_get_day)
    dayofweek = fields.Selection([
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
        ], 'Day of Week', compute=_get_day)

    passed = fields.Boolean("Passed", compute=_get_day)

    interval_ids = fields.One2many('hr.attendance.interval', 'day_id', string="Days")

    reason_1 = fields.Many2one('hr.attendance.type', "Reason 1", compute=_get_intervals, inverse=_set_intervals)
    reason_2 = fields.Many2one('hr.attendance.type', "Reason 2", compute=_get_intervals, inverse=_set_intervals)
    reason_3 = fields.Many2one('hr.attendance.type', "Reason 3", compute=_get_intervals, inverse=_set_intervals)
    reason_4 = fields.Many2one('hr.attendance.type', "Reason 4", compute=_get_intervals, inverse=_set_intervals)

    qty_1 = fields.Float("Qty 1", compute=_get_intervals, inverse=_set_intervals)
    qty_2 = fields.Float("Qty 2", compute=_get_intervals, inverse=_set_intervals)
    qty_3 = fields.Float("Qty 3", compute=_get_intervals, inverse=_set_intervals)
    qty_4 = fields.Float("Qty 4", compute=_get_intervals, inverse=_set_intervals)

    total = fields.Float("Total", readonly=True)
    total_e = fields.Float("Total Excepted", readonly=True)

    late_index = fields.Float("Lateness Index", compute=_get_late_index)
    absence_index = fields.Float("Absence Index", compute=_get_absence_index)

    schedule = fields.Many2one('resource.calendar', "Working Schedule")


class HrAttendanceInterval(models.Model):
    _name = 'hr.attendance.interval'
    _description = "Attendance Interval"

    day_id = fields.Many2one('hr.attendance.day', 'Day')
    date = fields.Date("Date", related="day_id.date", store=True, readonly=True)

    reason = fields.Many2one('hr.attendance.type', "Reason")
    qty = fields.Float("Qty")

    sequence = fields.Integer(default=1)


class HrAttendanceType(models.Model):
    _name = 'hr.attendance.type'
    _description = "Attendance Type"

    name = fields.Char("Description")
    code = fields.Char("Code", limit=5)

    att_type = fields.Selection([
        ('work', 'Attendance'),
        ('extra', 'Extra Attendance'),
        ('absn', 'Absence')
        ], 'Attendance Type', required=True, index=True, default='absn')
