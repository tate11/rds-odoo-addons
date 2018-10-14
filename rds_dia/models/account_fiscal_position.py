'''
Created on Sep 18, 2018

@author: mboscolo
'''
from odoo import api
from odoo import fields
from odoo import models
from odoo import _


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    dia_code = fields.Char("Codice Dia")
