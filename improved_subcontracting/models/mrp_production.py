# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_subcontracting = fields.Boolean("Subcontracted Production")

class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    
    @api.depends('subcontractor_id', 'bom_id')
    def _compute_available_operations(self):
        ops = self.env['bom.supplierinfo'].sudo()
        for i in self:
            if (i.subcontractor_id == False) or (i.bom_id == False):
                i.available_operations = False
                continue
            i.available_operations = ops.search([('name', '=', i.subcontractor_id.id), ('bom_id', '=', i.bom_id.id)])

    @api.depends('bom_id')
    def _compute_available_subcontractors(self):
        locs = self.env['stock.location'].sudo()
        for i in self:
            i.available_subcontractors = i.sudo().bom_id.seller_ids.mapped(lambda x: x.name).filtered(lambda x: locs.search([('partner_id', '=', x.id)]))

    @api.depends('location_src_id')
    def _compute_subcontractor(self):
        for i in self:
            if i.picking_type_id.is_subcontracting:
                if i.location_src_id.partner_id in i.available_subcontractors:
                    i.subcontractor_id = i.location_src_id.partner_id

    @api.one
    def _set_subcontractor(self):
        if self.subcontractor_id:
            loc = self.env['stock.location'].sudo().search([('partner_id', '=', self.subcontractor_id.id)], limit=1)
            if loc:
                self.write({'location_src_id': loc.ids[0], 'location_dest_id': loc.ids[0]})

    @api.onchange('subcontractor_id')
    def _upd_subcontractor(self):
        if self.subcontractor_id:
            loc = self.env['stock.location'].sudo().search([('partner_id', '=', self.subcontractor_id.id)], limit=1)
            if loc:
                self.update({'location_src_id': loc.ids[0], 'location_dest_id': loc.ids[0]})

    subcontracting_po = fields.Many2one('purchase.order', string="Subcontrating PO")

    available_subcontractors = fields.Many2many('res.partner', compute=_compute_available_subcontractors)
    subcontractor_id = fields.Many2one('res.partner', string="Subcontractor", inverse='_set_subcontractor', compute="_compute_subcontractor")
    
    available_operations = fields.Many2many('bom.supplierinfo', compute=_compute_available_operations)
    subcontracted_operations = fields.Many2many('bom.supplierinfo', string="Subcontracted Operations")
    
    @api.model
    def create(self, vals):
        a = super(MrpProduction, self).create(vals)

        a.subcontracted_operations = a.available_operations and a.available_operations[0]

        if a.subcontractor_id and a.subcontracted_operations:
            Po = self.env['purchase.order'].sudo()
            Pol = self.env['purchase.order.line'].sudo()

            po = Po.create(a._prepare_subcontract_po())
            for operation in a.subcontracted_operations:
                Pol.create(a._prepare_purchase_order_line(po, operation))
            a.subcontracting_po = po
        return a
    
    def _prepare_subcontract_po(self):
        partner = self.subcontractor_id
        fpos = self.env['account.fiscal.position'].with_context(force_company=self.company_id.id).get_fiscal_position(partner.id)

        return {
            'partner_id': partner.id,
            'company_id': self.company_id.id,
            'currency_id': partner.with_context(force_company=self.company_id.id).property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
            'origin': self.origin or self.name,
            'payment_term_id': partner.with_context(force_company=self.company_id.id).property_supplier_payment_term_id.id,
            'date_order': self.date_planned_start,
            'fiscal_position_id': fpos,
            'production_ids': (4, self.ids[0])
        }

    @api.multi
    def _prepare_purchase_order_line(self, po, operation):
        supplier = self.subcontractor_id

        taxes = self.product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes) if fpos else taxes

        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == self.company_id.id)

        price_unit = self.env['account.tax']._fix_tax_included_price_company(operation.price, operation.product_tmpl_id.supplier_taxes_id, taxes_id, self.company_id.id) if operation else 0.0
        if price_unit and operation and po.currency_id and operation.currency_id != po.currency_id:
            price_unit = operation.currency_id.compute(price_unit, po.currency_id)

        product_lang = self.product_id.with_context({
            'lang': supplier.lang,
            'partner_id': supplier.id,
        })
        service_lang = operation.product_tmpl_id.with_context({
            'lang': supplier.lang,
            'partner_id': supplier.id,
        })

        name = service_lang.display_name + ": " + (product_lang.default_code and "[%s]" % product_lang.default_code or "") + product_lang.display_name
        if operation.product_name or operation.product_code:
            name += _('\nYour Reference: ') + (operation.product_code and "[%s]" % operation.product_code or "") + (operation.product_name and "[%s]" % operation.product_name or "")
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return {
            'name': name,
            'product_qty': self.product_uom_id._compute_quantity(self.product_qty, operation.product_tmpl_id.uom_po_id),
            'product_id': operation.product_tmpl_id.id,
            'product_uom': operation.product_tmpl_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': self.date_planned_start,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'order_id': po.id,
        }

    def show_subc_po(self):
        action = self.env.ref('purchase.purchase_form_action')
        result = action.read()[0]
        result['domain'] = []
        result['context'] = {}
        
        res = self.env.ref('purchase.purchase_order_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['res_id'] = self.subcontracting_po.id
        return result