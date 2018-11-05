# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import models, fields, api

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    time_logging = fields.Selection([('standard', 'Interface-Detection'), ('manual', 'Manual')],
                                     default='standard', string="Time Logging", required=True)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    time_logging = fields.Selection([('standard', 'Interface-Detection'), ('manual', 'Manual')], string="Time Logging", related="workcenter_id.kiosk_type")

    def open_tablet_view(self):
        self.ensure_one()
        if not self.is_user_working and (self.working_state != 'blocked'):
            self.button_start()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder',
            'views': [[self.env.ref('mrp_workorder.mrp_workorder_view_form_tablet').id, 'form']],
            'res_id': self.id,
            'target': 'fullscreen',
            'flags': {
                'headless': True,
                'form_view_initial_mode': 'edit',
            },
        }

    @api.multi
    def button_start(self):
        self.ensure_one()

        if (self.time_logging == 'manual') and (self.state == 'progress'):
            return True

        return super(MrpWorkorder, self).button_start()

    @api.multi
    def button_pending(self):
        if self.time_logging == 'manual':
            return True
            
        self.end_previous()
        return True