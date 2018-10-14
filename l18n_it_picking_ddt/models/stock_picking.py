from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import base64, logging

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    reason_id =  fields.Many2one('stock.picking.reason', string="Default reason")
    ddt_type = fields.Selection(selection=[('none','No DDT'),('outgoing','Outgoing'),('incoming','Incoming')], required=True, default='none', string="DDT Type")

    @api.onchange('code')
    def set_ddt_required(self):
        if self.code in ['internal', 'mrp_operation']:
            self.ddt_type = 'none'
        elif self.code == 'outgoing':
            self.ddt_type = 'outgoing'
        else:
            self.ddt_type = 'incoming'

    @api.multi
    def write(self, vals):
        if vals.get('ddt_type', False):
            if bool(self.env['stock.picking'].sudo().search([('picking_type_id', 'in', self.ids)])):
                raise ValidationError(_('Cannot change DDT type of an operation that has pickings!'))
                
        return super(StockPickingType, self).write(vals)

class StockPickingGoodsDescription(models.Model):
    _name = 'stock.picking.goods_description'
    _description = "Description of Goods"

    name = fields.Char('Description of Goods', required=True, readonly=False)
    note = fields.Text('Notes')


class StockPickingReason(models.Model):
    _name = 'stock.picking.reason'
    _description = 'Transfer Reason'

    name = fields.Char('Transfer Reason', size=64, required=True, readonly=False)
    code = fields.Char('Code', size=8, required=True, readonly=False)
    ddt_type = fields.Selection(selection=[('none','No DDT'),('outgoing','Outgoing'),('incoming','Incoming')], required=True, default='none', string="DDT Type")
    sequence_id = fields.Many2one('ir.sequence', 'DDT Sequence', required=False)

    note = fields.Text('Notes')

class PickingDDT(models.Model):
    _inherit = 'stock.picking'

    partner_order_id = fields.Many2one('res.partner', "Partner", related="sale_id.partner_id")
    partner_invoice_id = fields.Many2one('res.partner', "Invoice Address", related="sale_id.partner_invoice_id")

    @api.one
    @api.depends('package_ids', 'weight_bulk', 'shipping_weight_free')
    def _compute_shipping_weight(self):
        if bool(self.shipping_weight_free):
            self.shipping_weight = self.shipping_weight_free
        else:
            self.shipping_weight = self.weight_bulk + sum([pack.shipping_weight for pack in self.package_ids])
        
    def _set_shipping_weight(self):
        self.shipping_weight_free = self.shipping_weight

    ddt_type = fields.Selection(selection=[('none','No DDT'),('outgoing','Outgoing'),('incoming','Incoming')], required=True, readonly=True, string="DDT Type", related="picking_type_id.ddt_type")

    ddt_number = fields.Char(string="DDT No.", copy=False)

    notes = fields.Text(string="Notes", copy=False)

    transport_partner_id =  fields.Many2one('res.partner', "Carrier Address", readonly=True, related="carrier_id.transport_partner_id")

    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of goods')
    reason_id = fields.Many2one('stock.picking.reason', 'Reason for Transfer')

    shipping_weight_free = fields.Float("Weight in Kilograms")
    shipping_weight = fields.Float(compute=_compute_shipping_weight, inverse=_set_shipping_weight)

    incoterm = fields.Many2one(
        'stock.incoterms', 'Incoterms',
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    def button_validate(self):
        if self.ddt_type == 'outgoing':
            err = []
            err += (not self.carrier_id) and [_("• Carrier isn't set")] or []
            err += (not self.goods_description_id) and [_("• Goods description isn't set")] or []
            err += (not self.reason_id) and [_("• Transfer Reason isn't set")] or []
            err += (not self.incoterm) and [_("• Incoterm isn't set")] or []
            err += (self.shipping_weight == 0) and [_("• Shipping Weight is zero")] or []
            err += (self.number_of_packages == 0) and [_("• Number of packages is zero")] or []
            err += ((self.ddt_type == 'incoming') and (self.ddt_number == False)) and  [_("• DDT Number not set")] or []

            if err:
                raise ValidationError(_("Cannot validate DDT due to missing information:\n") + ",\n".join(err) + ".")
            

        return super(PickingDDT, self).button_validate()

    def action_done(self):
        res = super(PickingDDT, self).action_done()
        if res and (self.ddt_type == 'outgoing'):
            if not self.reason_id.sequence_id:
                raise UserError(_("No sequence configured for this transfer reason!"))
            self.ddt_number = self.reason_id.sequence_id.next_by_id()
            
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('ddt_number', operator, name)] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, (rec.ddt_number and ('%s (%s)' % (rec.ddt_number, rec.name)) or rec.name)))
        return res

class Delivery(models.Model):
    _inherit = 'delivery.carrier'

    transport_partner_id =  fields.Many2one('res.partner', "Partner")

    @api.multi
    def write(self, vals):
        if bool(self.env['stock.picking'].sudo().search([('carrier_id', 'in', self.ids)])):
            raise ValidationError(_('Cannot change a delivery method that has pickings!'))

        return super(Delivery, self).write(vals)