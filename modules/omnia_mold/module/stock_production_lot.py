'''
Created on 20 Mar 2018

@author: mboscolo
'''

from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api


class MrpRutingWorkorder(models.Model):
    _inherit = 'stock.production.lot'

    n_shots_guarantee = fields.Integer(_('Number of guarantee shot'),
                                       default=0)
    n_shots = fields.Integer(_('Actual shot'),
                             default=0)

    @api.multi
    def _no_more_guarantee(self):
        for stock_production_lot in self:
            stock_production_lot.no_more_guarantee = stock_production_lot.n_shots_guarantee < stock_production_lot.n_shots

    no_more_guarantee = fields.Boolean(compute=_no_more_guarantee,
                                       string=_('Out Of Guarantee'))

    @api.multi
    def register_shot(self):
        for stock_production_lot in self:
            stock_production_lot.n_shots += 1
