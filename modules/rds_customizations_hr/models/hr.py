# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

'''
#
#   This whole section was added to ease contract info lookup for non-hr management personell.
#   At RDS we want production officers to know contract type and/or expiry of their personell,
#   but we don't want to grant access to the actual contracts.
#   
#   We also add an icon to Employee Tags which is used in employee badge for flavouring.
#
'''

from odoo import api, fields, models

class Employee(models.Model):
    
    _name = 'hr.employee'
    _inherit = ['hr.employee']

    @api.one
    def _compute_contract_info(self):
        # Computed as sudo because not all users have access to hr.contract.
        all_emp_contracts = self.sudo().env['hr.contract'].search(['&', ('state','in', ['open', 'pending','close']), ('employee_id', '=', self.ids[0])]).sorted(key=lambda r: r.date_start)
        running_contracts = all_emp_contracts.filtered(lambda s: s.state in ['open', 'pending']).sorted(key=lambda r: r.date_start)
        self.fixed_term = True

        if all_emp_contracts:
            self.first_employed = all_emp_contracts[0].date_start

            if running_contracts:
                self.current_contract_start = running_contracts[0].date_start
                self.current_contract_end = running_contracts[0].date_end
                if running_contracts.filtered(lambda x: x.date_end == False):
                    self.fixed_term = False
            else:
                self.last_employed = all_emp_contracts[0].date_end

    def _search_is_fixed_term(self, operator, value):
        non_expiring = self.sudo().env['hr.contract'].search(['&', ('state', 'in', ['open', 'pending']), ('date_end', '!=', False)])
        emp = []
        for i in non_expiring:
            emp.append(i.employee_id.id)
        
        if ((operator == '=') and (value == True)) or ((operator == '!=') and (value == False)):
            return [('id', 'in', emp)]
        else:
            return ['!', ('id', 'in', emp)]


    first_employed = fields.Date(string="First Assumption", compute='_compute_contract_info')
    last_employed = fields.Date(string="Left Since", compute='_compute_contract_info')

    current_contract_start = fields.Date(string="Current Contract Start", compute='_compute_contract_info')
    current_contract_end = fields.Date(string="Current Contract End", compute='_compute_contract_info')

    fixed_term = fields.Boolean(string="Fixed-Term", compute="_compute_contract_info", search="_search_is_fixed_term")

    is_subworker = fields.Boolean(string="Subcontracted Worker", default=False)


class EmployeeCategory(models.Model):

    _inherit = ['hr.employee.category']

    icon = fields.Binary(
        "Photo", attachment=True,
        help="This field holds an icon to be used as a badge on various reports.")
    # Added for flavouring reports or employee badges