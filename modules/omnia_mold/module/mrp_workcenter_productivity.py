'''
Created on 20 Mar 2018

@author: mboscolo
'''

from odoo import api
from odoo import fields
from odoo import models
from odoo import _


class ProductionWorcenter(models.Model):
    _inherit = 'mrp.workcenter.productivity'
    produced_qty = fields.Float(_('Produced Qty'))
