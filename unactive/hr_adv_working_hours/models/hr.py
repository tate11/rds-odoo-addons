# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models
import logging

'''
Description:
    Implements management of employees' working schedules with shift and forward planning.
        - List: A list of all employees, by department, with the respective schedule.
        - Shift Report: A report for a single shift in hierarchical form.
          Hierarchy is not inherited from manager relationship. Instead, it's calculated from Job Sequence.
          It is possible to apply styles based on job to this report.
'''

class Employee(models.Model):
    
    _name = 'hr.employee'
    _inherit = ['hr.employee']

    next_week_resource_calendar_id = fields.Many2one('resource.calendar', 'Next Shift')
    
    shift_worker = fields.Boolean(string="Shift Worker", oldname='does_turns', default=False) # This flag is for lookup **and** auto turn reassignment

    @api.model
    def _cron_rotate_shifts(self):
        for emp in self.search([]):
            nw = emp.next_week_resource_calendar_id

            if (not emp.shift_worker) and (not nw):
                continue

            if nw:
                emp.write({'resource_calendar_id': nw.id, 'next_week_resource_calendar_id': emp.shift_worker and nw.get_next().id or nw.id})
            else:
                nw = emp.resource_calendar_id.get_next()
                emp.write({'resource_calendar_id': nw.id, 'next_week_resource_calendar_id': nw.get_next().id})


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'
    _order = "name"

    # TODO: This could be better, perhaps adding a dedicated model?
    #       Current implementation is ligher on the db but perhaps not so intuitive for end-users. 
    #       Also add help on fields?
    
    shift_code = fields.Char(string='Shift Code', required=False)  # This identifies a sequence...
    shift_index = fields.Integer(string='Shift Index', required=False, default=0)  # and the resource.calendar's position in that sequence

    abstract = fields.Char("Written Form") # (report flavour)

    def get_next(self):
        self.ensure_one()
        if self.shift_code:
            shifts = self.search([('shift_code', '=', self.shift_code)]).sorted(lambda x: x.shift_index)
            _next = shifts.filtered(lambda x: x.shift_index >= self.shift_index)

            return _next[0] or shifts[0]
            
        return self

class Job(models.Model):

    _inherit = ['hr.job']
    _order = "priority"
    
    priority = fields.Integer(string='Priority', required=True, index=True, default=1000)  # TODO: Call it sequence?
    report_style = fields.Char(string='CSS Style on Reports') # TODO: Should be text.
