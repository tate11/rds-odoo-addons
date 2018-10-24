from odoo import models, fields, api, _

import logging

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    sequence_ddt_id = fields.Many2one('ir.sequence', 'DDT Sequence')


class Delivery(models.Model):
    _inherit = 'delivery.carrier'

    transport_partner_id =  fields.Many2one('res.partner', "Partner")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ddt_number = fields.Char("DDT Number", readonly=True)

    ddt_ids = fields.Many2many(
        comodel_name='stock.ddt',
        relation='picking_ddt_rel',
        string='DDT',
        copy=False)

    count_ddt = fields.Integer(string='# of DDTs',
                              compute='_compute_ddt')

    billing_status = fields.Selection([('none', 'Nothing to Bill'), ('todo', 'To Bill'), ('waiting', 'Waiting'), ('done', 'Billed')], 
                                      "Billing Status", readonly=True, required=True, compute='_compute_billing_status', default="none", store=True)

    @api.depends('ddt_ids')
    def _compute_ddt(self):
        for picking in self:
            picking.count_ddt = len(picking.ddt_ids) if picking.ddt_ids else 0

    @api.one
    @api.depends('ddt_ids', 'ddt_ids.state', 'picking_type_code', 'state')
    def _compute_billing_status(self):
        if (self.state != 'done') or (self.picking_type_code not in ['outgoing', 'incoming']):
            self.billing_status = 'none'
        elif self.ddt_ids.filtered(lambda x: x.state in ['draft', 'waiting']):
            self.billing_status = 'waiting'
        elif self.ddt_ids.filtered(lambda x: x.state == "done"):
            self.billing_status = 'done'
        else:
            self.billing_status = 'todo'

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
    def action_done(self):
        result = super(StockPicking, self).action_done()
    
        if result and (self.picking_type_code == 'outgoing'):      
            ddt = self.env['stock.ddt'].search([('partner_id', '=', self.partner_id.id), ('picking_type_id', '=', self.picking_type_id.id), ('state', 'in', ['draft','waiting'])], limit=1)
            ddt = ddt and ddt[0]

            if not ddt:
                ddt = self.env['stock.ddt'].create(
                    {
                        'name': self.picking_type_id.sequence_ddt_id.next_by_id(),
                        'picking_type_id': self.picking_type_id.id,
                        'partner_id': self.partner_id.id,
                        'state': 'waiting',
                        'partner_invoice_id': self.sale_id and self.sale_id.partner_invoice_id.id,
                        'carrier_id': self.carrier_id and self.carrier_id.id,
                        'incoterm': self.sale_id and self.sale_id.incoterm.id,
                        'picking_ids': [(4, self.id)]
                    }
                )
            else:
                ddt.write({'picking_ids': [(4, self.id)]})

        return result

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
            res.append((rec.id, (rec.ddt_number and ('%s (%s)' % (rec.name, rec.ddt_number)) or rec.name)))
        return res