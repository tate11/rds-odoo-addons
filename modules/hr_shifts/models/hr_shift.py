# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class HrShift(models.Model):
    _name = 'hr.shift'
    _description = 'Work Shifts'

    def _compute_employees_count(self):
        for i in self:
            i.employee_count = len(i.employee_ids)

    def _get_current(self):
        for i in self:
            current = i.line_ids.filtered(lambda x: x.current)

            if len(current) == 1:
                i.current_resource_calendar_id = current.name


    name = fields.Char("Name", required=True)
    date = fields.Date("Next Rotation")
    interval = fields.Integer("Interval")

    line_ids = fields.One2many('hr.shift.line', 'shift_id', "Schedules")
    
    employee_ids = fields.One2many('hr.employee', 'shift_id', "Employees")
    employee_count = fields.Integer("# of Employees", compute=_compute_employees_count)

    current_resource_calendar_id = fields.Many2one('resource.calendar', 'Schedule', compute=_get_current)

    def action_shift(self):
        self.ensure_one()

        current = self.line_ids.filtered(lambda x: x.current)
        if not current:
            self.line_ids[0].toggle()
            return

        _next = self.line_ids.filtered(lambda x: x.sequence > current.sequence)

        if _next:
            _next[0].toggle()
        else:
            self.line_ids[0].toggle()

    def action_see_employees(self):
        self.ensure_one()

        return {
            'name': _('Employees'),
            'domain': [('id', 'in', self.employee_ids.ids)],
            'res_model': 'hr.employee',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80
        }
            
    def cron_shift(self):
        to_shift = self.search([('date', '<=', fields.Date.to_string(fields.Date.today()))])
        for shift in to_shift:
            shift.action_shift()

            shift.date = shift.date + timedelta(shift.interval)

    def name_get(self):
        return [(record.id, record.name + ("" if not record.current_resource_calendar_id else " - {}".format(record.current_resource_calendar_id.name))) for record in self]

class HrShiftLine(models.Model):
    _name = 'hr.shift.line'
    _description = 'Work Shifts Lines'
    _order = "sequence"

    name = fields.Many2one('resource.calendar', 'Schedule', required=True)
    shift_id = fields.Many2one('hr.shift', 'Shift', ondelete="cascade", required=True)

    sequence = fields.Integer()
    current = fields.Boolean("Current")

    @api.model_create_multi
    def create(self, vals_list):
        i = 10
        recs = self

        for vals in vals_list:
            vals['sequence'] = i
            recs |= super(HrShiftLine, self).create(vals)
            i += 10

        return recs

    def toggle(self):
        self.ensure_one()

        for i in self.shift_id.line_ids:
            i.current = False

        self.current = True

        for emp in self.shift_id.employee_ids:
            emp.resource_calendar_id = self.name