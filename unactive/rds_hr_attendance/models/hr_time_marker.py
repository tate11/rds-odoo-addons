from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import image
import logging

class TimeMarker(models.Model):
    _name = 'rds.hr.timemarker'

    name = fields.Char("Nome Marcatempo")
    address = fields.Char("Indirizzo IP")

    dep = fields.Many2many('hr.department', string="Reparti")
    dep_do = fields.Selection([('in', 'Limita a'),('not in', 'Escludi')], string="Filtro su Dipartimento")
    emp = fields.Many2many('hr.employee', string="Dipendenti")
    emp_do = fields.Selection([('in', 'Limita a'),('not in', 'Escludi')], string="Filtro su Impiegato")

    def is_employee_allowed(self, idx):
        domain = [('id', '=', idx)]
        if (bool(self.dep_do) and bool(self.dep)):
            domain = expression.AND([domain, [('department_id', self.dep_do, self.dep.ids)]])
        if (bool(self.emp_do) and bool(self.emp)):
            domain = expression.AND([domain, [('id', self.emp_do, self.emp.ids)]])
        
        return bool(self.sudo().env['hr.employee'].search(domain))

    @api.model
    def download_employees(self, mid):
        self = self.browse(mid)
        domain = []
        if (bool(self.dep_do) and bool(self.dep)):
            domain = expression.AND([domain, [('department_id', self.dep_do, self.dep.ids)]])
        if (bool(self.emp_do) and bool(self.emp)):
            domain = expression.AND([domain, [('id', self.emp_do, self.emp.ids)]])
        
        employees = self.sudo().env['hr.employee'].search(domain)
        return employees.mapped(lambda x: (
                                            x.id,
                                            x.name,
                                            x.barcode,
                                            image.image_resize_image(x.image),
                                            x.write_date,                                          
                                          ))

    @api.model
    def read_markings(self, markings):
        stack = []
        for i in markings:
            employee = self.sudo().env['hr.employee'].browse(i[1])
            employee.rds_attendance_register(i[2])
            stack.append(i[0])

        return stack