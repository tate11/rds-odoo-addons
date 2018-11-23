'''
Created on 28 Jul 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import _
from odoo import api


class StockMove(models.Model):
    _inherit = "stock.move"

    is_materozza = fields.Boolean("Is Materozza move", default=False)
