from odoo import api, fields, models

from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

import base64, logging

def df2d(field):
    return datetime.strptime(field, DEFAULT_SERVER_DATE_FORMAT)

class PayrollPrinter(models.TransientModel):
    _name = 'payroll.printer'


    gis_payroll = fields.Binary(readonly=True, string="File Paghe")
    gis_payroll_name = fields.Char('Filename di Payroll Gis',
                             size=255,
                             readonly=True)
    payroll_text = fields.Text(string="Stringhe Paghe")

    date_from = fields.Date(string="Stampa da", default=fields.Date.today())
    date_to = fields.Date(string="Stampa a", default=fields.Date.today())

    mode = fields.Selection(selection=[
        ('all'    , 'Tutte'),
        ('dept'   , 'Per Reparto'),
        ('person' , 'Per Dipendente')
    ], required=True, default="all", string="Buste paghe da stampare", help="Modo di selezione")
    
    state = fields.Selection(selection=[
        ('setup', 'Setup'),
        ('ready', 'Ready')
    ], required=True, default="setup", string="Stato")

    subworkers = fields.Selection(selection=[
        ('yes', 'Includi'),
        ('no', 'Escludi'),
        ('only', 'Stampa Solo Interinali')
    ], required=True, default="no", string="Stampa Interinali")
    
    employee_ids = fields.Many2many('hr.employee', string="Dipendenti")
    department_ids = fields.Many2many('hr.department', string="Reparti")


    def get_working_units(self):
        wus = self.sudo().env['rds.hr.working.unit'].search([('date', '>=', df2d(self.date_from).strftime(DEFAULT_SERVER_DATE_FORMAT)),
                                                              ('date', '<=', df2d(self.date_to).strftime(DEFAULT_SERVER_DATE_FORMAT))])
        if self.subworkers == 'no':
            wus = wus.filtered(lambda x: x.employee_id.is_subworker == False)
        elif self.subworkers == 'only':
            wus = wus.filtered(lambda x: x.employee_id.is_subworker == True)
        
        if self.mode == 'dept':
            return wus.filtered(lambda x: x.department_id in self.department_ids)
        elif self.mode == 'person':
            return wus.filtered(lambda x: x.employee_id in self.employee_ids)
        else:
            return wus

    def get_gis_payroll(self):
        if bool(self.date_from) & bool(self.date_to) & (not bool(self.gis_payroll)):
            text_stream = ''
            for t in self.get_working_units():
                text_stream += t.payroll_gis if t.payroll_gis else ''
            
            vals = {'state': 'ready'}
            vals['gis_payroll']  = base64.encodestring(text_stream.encode())
            vals['gis_payroll_name']  = 'GIS.txt'
            vals['payroll_text'] = text_stream

            new_id = self.create(vals)

            return {
                'name': 'Prepara Marcatore',
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'payroll.printer',
                'target': 'self',
                'res_id': new_id.id,
                'type': 'ir.actions.act_window',
                }

    @api.multi
    def print_payroll_report(self):
        return self.env.ref('rds_hr_attendance.action_report_payroll').report_action(self)

    def days_by_employee(self):
        wus = self.get_working_units()
        employees = list(set([x.employee_id for x in wus]))
        
        days = []
        day = datetime.strptime(self.date_from, DEFAULT_SERVER_DATE_FORMAT)
        day_end = datetime.strptime(self.date_to, DEFAULT_SERVER_DATE_FORMAT)
        WEEKDAYS=['L', 'M', 'M', 'G', 'V', 'S', 'S']
        while day <= day_end:
            days += [day]
            day = day + timedelta(1)

        return sorted([[x,[[d.strftime("%d-%m-%Y"), wus.filtered(lambda y: y.employee_id == x).filtered(lambda k: k.date == d.strftime(DEFAULT_SERVER_DATE_FORMAT)), WEEKDAYS[d.weekday()]] for d in days], wus.filtered(lambda y: y.employee_id == x).get_all_intervals().get_layouted_intervals(True)] for x in employees], key=lambda z: int(z[0].payroll_id))