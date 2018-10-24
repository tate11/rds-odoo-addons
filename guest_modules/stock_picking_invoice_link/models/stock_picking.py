# -*- coding: utf-8 -*-
# © 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2015-2016 AvanzOSC
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# © 2016 KTec S.r.l. (<http://www.ktec.it>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_ids = fields.Many2many(
        comodel_name='account.invoice', string='Invoices',
        compute="_compute_invoice_ids")
    invoice_count = fields.Integer(string='Invoices number', compute="_compute_invoice_ids")

    @api.multi
    def _compute_invoice_ids(self):
        for picking in self:
            invoices = self.env['account.invoice']
            for line in picking.move_lines:
                invoices |= line.invoice_line_ids.mapped('invoice_id')
            picking.invoice_ids = invoices
            picking.invoice_count = len(invoices)


    @api.multi
    def action_view_invoices(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
