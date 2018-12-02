# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import api, fields, models, tools


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    owner_id = fields.Many2one('res.partner', 'Owner')
    owner_ref = fields.Char('Owner Reference')

    warranty_type = fields.Selection([
                                        ('none', 'No Warranty'),
                                        ('date', 'Time-Based'),
                                        ('process', 'Cycle Number')
                                     ], 'Warranty Type', default="none", required=True)

    warranted_cycles = fields.Integer('Warranted Cycles')
    cycles = fields.Integer('Effective Cycles')

    maintenance_color = fields.Integer('Maintenance Color', compute="_compute_maintenance_color")
    
    @api.multi
    def _compute_maintenance_color(self):
        for i in self:
            i.maintenance_color = 9 if (i.maintenance_open_count >= 1) else 10
  
    @api.multi
    def log_consumption(self, cycles):
        for i in self:
            i.cycles += int(cycles)
