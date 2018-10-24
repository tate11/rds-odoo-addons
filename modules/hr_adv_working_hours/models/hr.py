# Intended for sole use by RDS Moulding Technology SpA. See README file.

from odoo import api, fields, models
import logging


    #------------------------------------#
    #
    #   This whole file was added to manage rotating shifts.
    #   The "Jobs" inherit was added to flavour shifts reports.
    #
    #------------------------------------#



class Employee(models.Model):
    
    _name = 'hr.employee'
    _inherit = ['hr.employee']

    next_week_resource_calendar_id = fields.Many2one('resource.calendar', 'Next Shift')
    
    does_turns = fields.Boolean(string="Shift Worker", default=False) # This flag is for lookup **and** auto turn reassignment

    @api.model
    def _cron_rotate_shifts(self):
        for emp in self.search([]):
            nw = emp.next_week_resource_calendar_id

            if (not emp.does_turns) and (not nw):
                continue

            if nw:
                emp.write({'resource_calendar_id': nw.id, 'next_week_resource_calendar_id': emp.does_turns and nw.get_next().id or nw.id})
            else:
                nw = emp.resource_calendar_id.get_next()
                emp.write({'resource_calendar_id': nw.id, 'next_week_resource_calendar_id': nw.get_next().id})




class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'
    _order = "name"
    
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
    
    priority = fields.Integer(string='Priorità', required=True, index=True, default=1000)
    report_style = fields.Char(string='Kanban style sul report')
