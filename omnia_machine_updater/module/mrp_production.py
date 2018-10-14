'''
Created on 3 Aug 2018

@author: mboscolo
'''
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
import math
import logging


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    @api.multi
    def register_shot(self):
        for mrp_production_id in self:
            mold_id = mrp_production_id.mold_id
            if mold_id:
                mold_id.register_shot()
