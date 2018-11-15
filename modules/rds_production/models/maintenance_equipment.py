# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    owner_id = fields.Many2one('res.partner', 'Owner')
    owner_ref = fields.Char('Owner Reference')

    warranty_type = fields.Selection([
                                        ('none', 'No Warranty'),
                                        ('date', 'Time-Based'),
                                        ('process', 'Cycle Number'),
                                        ('component', 'Component Cycles')
                                     ], 'Warranty Type', default="none", required=True)

    warranted_cycles = fields.Integer('Warranted Cycles')
    cycles = fields.Integer('Effective Cycles')

    component_ids = fields.Many2many('maintenance.equipment.component', 'equipment_components', string='Components')

    maintenance_color = fields.Integer('Maintenance Color', compute="_compute_maintenance_color")
    
    @api.multi
    def _compute_maintenance_color(self):
        for i in self:
            i.maintenance_color = 9 if (i.maintenance_open_count >= 1) else 10
  
    @api.multi
    def log_consumption(self, cycles):
        components = self.env['maintenance.equipment.component']
        for i in self:
            i.cycles += int(cycles)
            components |= i.component_ids     
        for t in components:
            t.cycles += int(cycles)


class MaintenanceEquipmentComponent(models.Model):
    _name = 'maintenance.equipment.component'
    _description = 'Maintenance Equipment Component'


    equipment_ids = fields.Many2many('maintenance.equipment', 'equipment_components', string='Equipments')
    name = fields.Char("Component", required=True)
    description = fields.Char("Description")
    serial = fields.Char("Serial No.")
    cycles = fields.Integer("Sustained Cycles")
    warranted_cycles = fields.Integer("Warranted Cycles")