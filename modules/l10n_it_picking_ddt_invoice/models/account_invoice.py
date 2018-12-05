# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import models, fields, api, _

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def _compute_ddt_ids(self):
        for line in self:
            line.ddt_ids = line.sale_line_ids\
                .mapped(lambda x: x.move_ids)\
                .mapped(lambda x: x.picking_id)\
                .mapped(lambda x: x.ddt_ids)\
                .filtered(lambda x: x.state == 'done')

    ddt_ids = fields.Many2many("DDTs", compute=_compute_ddt_ids)
