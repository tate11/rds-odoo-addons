# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    sequence_ddt_id = fields.Many2one('ir.sequence', 'DDT Sequence')


class Delivery(models.Model):
    _inherit = 'delivery.carrier'

    transport_partner_id =  fields.Many2one('res.partner', "Partner")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ddt_ids = fields.Many2many(
        comodel_name='stock.ddt',
        relation='picking_ddt_rel',
        string='DDT',
        copy=False)

    count_ddt = fields.Integer(string='# of DDTs',
                              compute='_compute_ddt')
    
    @api.depends('ddt_ids')
    def _compute_ddt(self):
        for picking in self:
            picking.count_ddt = len(picking.ddt_ids) if picking.ddt_ids else 0

    billing_status = fields.Selection([('none', 'Nothing to Bill'), ('waiting', 'Waiting'), ('done', 'Billed')], 
                                      "Billing Status", readonly=True, default="none")

    @api.multi
    def action_view_ddt(self):
        ddts = self.mapped('ddt_ids')
        action = self.env.ref('l10n_it_picking_ddt.action_stock_view_ddts').read()[0]

        if len(ddts) > 1:
            action['domain'] = [('id', 'in', ddts.ids)]
        elif len(ddts) == 1:
            action['views'] = [(self.env.ref('l10n_it_picking_ddt.stock_view_ddts_form').id, 'form')]
            action['res_id'] = ddts.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_bill(self):
        dom = [('partner_id', '=', self.partner_id.id), ('picking_type_id', '=', self.picking_type_id.id), ('state', 'in', ['draft','waiting'])]
        ddt = self.env['stock.ddt'].search(dom + ([('name', '=', self.ddt_number)] if self.picking_type_code == 'incoming' else []), limit=1)
        ddt = ddt and ddt[0]

        if (not ddt):
            if (self.picking_type_code != 'incoming') and (not self.picking_type_id.sequence_ddt_id):
                raise ValidationError(_("A DDT numerator must be properly setup in the corresponding operation. Please ask your system admin correct the setup."))
            elif (self.picking_type_code == 'incoming') and (not self.ddt_number):
                raise ValidationError(_("To bill incoming pickings you need to specify a DDT number!"))

            vals =  {
                    'name': self.ddt_number if self.picking_type_code == 'incoming' else self.picking_type_id.sequence_ddt_id.next_by_id(),
                    'picking_type_id': self.picking_type_id.id,
                    'partner_id': self.partner_id.id,
                    'state': 'waiting',
                    'goods_description_id': self.goods_description_id.id,
                    'number_of_packages': self.number_of_packages,
                    'partner_invoice_id': self.sale_id and self.sale_id.partner_invoice_id.id,
                    'carrier_id': self.carrier_id and self.carrier_id.id,
                    'incoterm': self.incoterm.id,
                    'picking_ids': [(4, self.id)],
                    'note': self.note
                }
            ddt = self.env['stock.ddt'].create(vals)
        else:
            ddt.write({'picking_ids': [(4, self.id)]})

        self.billing_status = 'waiting'
  
    ddt_number = fields.Char(string="DDT No.", copy=False, states={'done': [('readonly', True)], 'cancelled': [('readonly', True)]})
    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of goods', states={'done': [('readonly', True)], 'cancelled': [('readonly', True)]})

    number_of_packages = fields.Integer("Number of Packages", states={'done': [('readonly', True)], 'cancelled': [('readonly', True)]})

    transport_partner_id = fields.Many2one('res.partner', "Carrier Address", readonly=True, related="carrier_id.transport_partner_id")

    @api.model
    def create(self, vals):
        if vals.get('sale_id', False):
            vals['incoterm'] = self.sudo().env['sale.order'].browse(vals.get('sale_id', False)).incoterm.id
        elif vals.get('purchase_id', False):
            vals['incoterm'] = self.sudo().env['purchase.order'].browse(vals.get('purchase_id', False)).incoterm_id.id

        return super(StockPicking, self).create(vals)

    incoterm = fields.Many2one(
        'account.incoterms', 'Incoterms',
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.", states={'done': [('readonly', True)], 'cancelled': [('readonly', True)]})

    def _set_shipping_weight(self):
        self.shipping_weight_free = self.shipping_weight

    @api.one
    @api.depends('package_ids', 'weight_bulk')
    def _compute_shipping_weight(self):
        if self.shipping_weight_free != 0:
            self.shipping_weight = self.shipping_weight_free
        else:
            self.shipping_weight = self.weight_bulk + sum([pack.shipping_weight for pack in self.package_ids])

    shipping_weight = fields.Float(inverse=_set_shipping_weight)

    shipping_weight_free = fields.Float("Weight in Kilograms")