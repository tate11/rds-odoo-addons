'''
Created on 18 Jul 2018

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


class ChangeProductionQty(models.TransientModel):
    _inherit = "change.production.qty"

    @api.multi
    def change_prod_qty(self):
        for wizard in self:
            production = wizard.mo_id
            super(ChangeProductionQty, self).change_prod_qty()
            if production.mold_id:
                for cavity in production.mold_id.mold_configuration:
                    if not cavity.exclude:
                        for bom_id in cavity.product_id.bom_ids:
                            _boms, exploded_lines = bom_id.explode(cavity.product_id,
                                                                   1,  # factor
                                                                   picking_type=bom_id.picking_type_id)
                            for bom_line, line_data in exploded_lines:
                                moves = production._update_raw_move(bom_line, line_data)
                                for move in moves:
                                    move.product_uom_qty = production.product_qty * line_data.get('qty', 1)
