# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import UserError


class AccountTax(models.Model):
    _inherit = 'account.tax'

    dia_code = fields.Char(size=2, oldname="legacy_dia_code", string='Dia Code')  # utile solo per la fase di import


class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    dia_code = fields.Char(size=6, string='Dia Code')

class FiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'
    
    dia_code = fields.Char(size=2, string='Dia Code')

