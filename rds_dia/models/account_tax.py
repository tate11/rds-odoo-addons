'''
Created on 6 Jun 2018

@author: mboscolo
'''
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import UserError


class AccountTax(models.Model):
    _inherit = 'account.tax'
    dia_legacy_code = fields.Char(size=2,
                                  string='Dia Legacy code')  # utile solo per la fase di import
