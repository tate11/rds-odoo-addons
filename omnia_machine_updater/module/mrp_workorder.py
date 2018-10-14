'''
Created on 3 Aug 2018

@author: mboscolo
'''


import datetime
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError
import logging
from dateutil.relativedelta import relativedelta


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def register_shot(self):
        for mrp_workorder_id in self:
            mrp_workorder_id.production_id.mold_id.register_shot()
