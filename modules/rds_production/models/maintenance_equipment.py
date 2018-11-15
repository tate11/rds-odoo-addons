# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    maintenance_color = fields.Integer('Maintenance Color', compute="_compute_maintenance_color")
    
    @api.multi
    def _compute_maintenance_color(self):
        for i in self:
            i.maintenance_color = 9 if (i.maintenance_open_count >= 1) else 10
  