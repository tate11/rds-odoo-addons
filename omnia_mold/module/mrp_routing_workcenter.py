'''
Created on 15 Mar 2018

@author: mboscolo
operation_id
'''
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    workcenter_ids = fields.Many2many('mrp.workcenter', compute="_get_workcenters", string="Centri di Lavoro")

    tools_ids = fields.Many2many('maintenance.equipment',
                              string='Tools')

    @api.multi
    def _get_workcenters(self):
        for i in self:
            i.workcenter_ids = i.operation_ids.mapped(lambda x: x.workcenter_id)

class MrpRutingWorkorder(models.Model):
    _inherit = 'mrp.routing.workcenter'

    #process_product = fields.Boolean(_('Process all products at once'))
    time_mount_machine = fields.Float("Mount Time")
