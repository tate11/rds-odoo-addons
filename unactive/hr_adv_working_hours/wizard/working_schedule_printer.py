# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

'''
Description:
    Implements a wizard used to print employees' working schedules. Supports two format:
        - List: A list of all employees, by department, with the respective schedule.
        - Shift Report: A report for a single shift in hierarchical form.
          Hierarchy is not inherited from manager relationship. Instead, it's calculated from Job Sequence.
          It is possible to apply styles based on job to this report.
'''

from odoo import api, fields, models
from odoo.osv import expression

from datetime import datetime, date, timedelta

class ResourceCalendar(models.Model):

    _inherit = 'resource.calendar'

    def get_layouted_employees(self, next_w=False, dom=[]):
        domain = [('next_week_resource_calendar_id', '=', self.ids[0])] if next_w else [('resource_calendar_id', '=', self.ids[0])]
        if dom:
            domain += dom

        employees = self.env['hr.employee'].search(domain)
        
        tot = len(employees)
        done = 0
        pr = 0
        layouted_employees = []

        while done < tot:
            emps = employees.filtered(lambda x: (x.job_id.priority <= pr) and (x.job_id.priority > pr-100)).sorted(lambda x: x.job_id.priority)
            if emps:
                layouted_employees += [emps]
                done += len(emps)
            pr += 100

        return layouted_employees


class WorkingSchedulePrinter(models.TransientModel):
    _name = 'working.schedule.printer'
    _description = "Schedule Printer"

    dep = fields.Many2many('hr.department', string="Departments")
    dep_do = fields.Selection([('in', 'Limit to'),('not in', 'Exclude')], string="Department Filter")
    emp = fields.Many2many('hr.employee', string="Employees")
    emp_do = fields.Selection([('in', 'Limit to'),('not in', 'Exclude')], string="Employee Filter")

    week = fields.Selection([
        ('this', 'This Week'),
        ('next', 'Next Week'),
        ], default='this')

    print_format = fields.Selection([
        ('list', 'List'),
        ('turn', 'Turns'),
        ], default='turn', required=True)
    
    def get_dom(self):
        domain = []
        if (bool(self.dep_do) and bool(self.dep)):
            domain = expression.AND([domain, [('department_id', self.dep_do, self.dep.ids)]])
        if (bool(self.emp_do) and bool(self.emp)):
            domain = expression.AND([domain, [('id', self.emp_do, self.emp.ids)]])
        return domain

    def get_report_obj(self):
        w = True if self.week == 'next' else False
        emps = self.env['hr.employee'].search(self.get_dom())        
        
        if self.print_format == 'turn':
            schedules = emps.mapped('resource_calendar_id') if self.week == 'this' else emps.mapped('next_week_resource_calendar_id') 
            schedules = schedules.filtered(lambda x: x.shift_code != False)
            obj = [(schedule, schedule.get_layouted_employees(w, self.get_dom())) for schedule in schedules]
            return obj
        else:
            departments = emps.mapped('department_id')
            obj = [(dep, emps.filtered(lambda x: x.department_id == dep)) for dep in departments]

            # TODO: Clean
            import logging
            logging.warning(obj)
            #

            return obj

    @api.multi
    def print_turns(self):
        return self.env.ref('hr_adv_working_hours.print_shift_sheet').report_action(self) if self.print_format == 'turn' else self.env.ref('hr_adv_working_hours.print_overall_schedule_list').report_action(self)

    def get_week(self):
        if self.week == 'this':
            mon = date.today() - timedelta(days=date.today().weekday())
            fri = mon + timedelta(5)            
        elif self.week == 'next':
            mon = date.today() - timedelta(days=date.today().weekday(), weeks=1) 
            fri = mon + timedelta(5)
        return [mon, fri]
