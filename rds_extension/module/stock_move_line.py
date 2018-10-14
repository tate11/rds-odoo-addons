'''
Created on Sep 12, 2018

@author: daniel
'''
from odoo import api
from odoo import fields
from odoo import models
from odoo import _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _compute_partner(self):
        for orderLineBrws in self:
            orderLineBrws.partner_id = False
            if orderLineBrws.move_id:
                if orderLineBrws.move_id.sale_line_id:
                    if orderLineBrws.move_id.sale_line_id.order_id:
                        orderLineBrws.partner_id = orderLineBrws.move_id.sale_line_id.order_id.partner_id.id

    partner_id = fields.Many2one('res.partner', string='Partner', compute=_compute_partner)
    ddt_number = fields.Char(related='picking_id.ddt_number', string=_('DDT Number'))
    pick_scheduled_date = fields.Date(related='picking_id.ddt_date', string=_('DDT Date'))


class WarehouseJournal(models.TransientModel):
    _inherit = 'warehouse.journal'
    
    @api.model
    def getRowVals(self, counter, moveLine, addQty, minusQty):
        ret = super(WarehouseJournal, self).getRowVals(counter, moveLine, addQty, minusQty)
        ret.append(moveLine.location_dest_id.dia_location or '')  # DEP
        ret.append(moveLine.picking_id.causale_dia.serie_description or '') # CAUSALE DEL MOVIMENTO
        return ret

    @api.model
    def getExportHeaders(self):
        ret = super(WarehouseJournal, self).getExportHeaders()
        ret.append('DEP')
        ret.append('CAUSALE DEL MOVIMENTO')
        return ret

