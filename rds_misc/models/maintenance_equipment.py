
from odoo import api, fields, models

class MaintenanceEquipment(models.Model):

    _inherit = 'maintenance.equipment'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
                
        recs = self.search(['|', ('name', operator, name), ('serial_no', operator, name), ] + args, limit=limit)

        return recs.name_get()