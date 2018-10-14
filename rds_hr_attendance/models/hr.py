# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from random import choice
from string import digits

from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, image
import logging, base64, datetime

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    extraordinary_policy = fields.Selection(selection=[
        ('fill_ignore', 'Flessibile'),
        ('fill_extr'  , 'Flessibile con Straordinari'),
        ('ignore'     , 'Rigido')
    ], required=True, default="ignore", string="Politica Orario", help="La politica da adottare in contabilizzazione per il lavoro fuori orario.")
    payroll_id = fields.Char(string="ID Paghe")
    payroll_bonus = fields.Selection(selection=[
        ('magp', 'Mag. 50% Notte, 25% Sera'),
        ('magn'  , 'Mag. 25% Notte, 20% Sera'),
    ], string="Bonus Paga")

    convoca = fields.Boolean(string="Convoca?")

    @api.model
    def timemarker_scan(self, markings):
        for i in markings:
            pass

    @api.model
    def rds_attendance_scan(self, barcode, time, ip):
        """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
            Returns either an action or a warning.
        """
        barcode = barcode.zfill(10)

        def get_cut_base16(string):
            try:
                return [str(int(barcode[4:], 16)).zfill(10), str(int(barcode[3:], 16)).zfill(10)]
            except ValueError:
                return []
            

        barcode_array = [barcode] + get_cut_base16(barcode)

        marker = self.sudo().env['rds.hr.timemarker'].search([('address', '=', ip)], limit=1)

        if not marker:
            return {'result': 'error', 'error_text': 'Questo marcatempo non è registrato! (IP: %s)' % ip}
            
        employee = self.sudo().search([('barcode', 'in', barcode_array)], limit=1)


        if employee:


            if marker[0].is_employee_allowed(employee.ids[0]):
                return employee.rds_attendance_register(time)
            else:
                return {'result': 'error', 'error_text': 'Non ti è permesso marcare su questo terminale.'}


        else:
            return {'result': 'error', 'error_text': 'Questo badge non è registrato: %(barcode)s' % {'barcode': barcode}}

    @api.multi
    def rds_attendance_register(self, time):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()
        result = {
            'result': 'success',
            'employee_name': self.name,
            'employee_image_url': "/hr/portrait?uid=%d" % self.ids[0],
            'cta': self.convoca
        }

        self.convoca = False

        if self.attendance_state != 'checked_in':
            result['in'] = True
        else:
            result['in'] = False

        if time:
            self.sudo().attendance_do(time)

        self.env.cr.commit()
        return result

    @api.multi
    def attendance_do(self, time):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        if len(self) > 1:
            raise exceptions.UserError(_('Cannot perform check in or check out on multiple employees.'))
        action_date = time

        try:
            datetime.datetime.strptime("action_date", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            action_date = action_date[:10] + " " + action_date[11:19]
        
        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            return self.env['hr.attendance'].create(vals)
        else:
            attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
            if attendance:
                attendance.check_out = action_date
            else:
                raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                    'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.name, })
            return attendance