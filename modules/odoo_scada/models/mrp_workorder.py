import datetime
from odoo import fields
from odoo import models
from pytz import timezone, UTC

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    kiosk_type = fields.Selection([('standard', 'Manual Advancement'),
                                   ('auto', 'Auto Advancement')], related="workcenter_id.kiosk_type")

    def open_tablet_view(self):
        self.ensure_one()
        if self.kiosk_type == "standard":
            if not self.is_user_working and self.working_state != 'blocked':
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


        elif self.kiosk_type == "auto":
            action = self.env.ref('odoo_scada.mrp_workcenter_scada_panel', False)
            return {
                'name': action.name,
                'tag': action.tag,
                'data': self.build_scada(),
                'type': 'ir.actions.client'
            }

    def build_scada(self):
        self.ensure_one()
        last_efficiency = self.time_ids and self.time_ids[0]
        user_tz = self.env.user.tz or 'UTC'
        
        return {
            'id': self.id,
            'name': self.name,

            'workcenter_id': {
                'id': self.workcenter_id.id,
                'oee': self.workcenter_id.oee,
                'name': self.workcenter_id.name
            },

            'production_id': {
                'id': self.production_id.id,
                'name': self.production_id.name
            },

            'last_efficiency': {
                'date': (last_efficiency.date_end 
                         and timezone('UTC').localize(last_efficiency.date_end).astimezone(timezone(user_tz))
                         or timezone('UTC').localize(last_efficiency.date_start).astimezone(timezone(user_tz))),
                'status': last_efficiency.loss_id.name,
                'status_type': last_efficiency.loss_id.loss_type
            }
        }

    