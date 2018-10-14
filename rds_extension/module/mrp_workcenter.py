'''
Created on 27 Jun 2018

@author: mboscolo
'''


from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api


def empyStringIfFalse(value):
    if not value:
        return ""
    return value


class MrpRutingWorkorder(models.Model):
    _inherit = 'mrp.workcenter'

    @api.multi
    def name_get(self):
        """
            get the name of the work center
        """
        out = []
        for workcenter_id in self:
            name = empyStringIfFalse(workcenter_id.code) + ' - ' + empyStringIfFalse(workcenter_id.name)
            out.append((workcenter_id.id, name))
        return out

    @api.model
    def name_search(self, name, args=[], operator='ilike', limit=100):
        if name:
            args = [('name', operator, name),
                    ('code', operator, name)] + args
        return self.search(args, limit=limit).name_get()
