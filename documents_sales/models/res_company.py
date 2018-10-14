# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    dms_sale_settings = fields.Boolean()
    sale_folder = fields.Many2one('documents.folder',
                                     default=lambda self: self.env.ref('documents.documents_sales_folder',
                                                                       raise_if_not_found=False))
    sale_tags = fields.Many2many('documents.tag', 'sale_tags_table')

    @api.multi
    def write(self, values):
        for company in self:
            if not company.dms_sale_settings and values.get('dms_sale_settings'):
                attachments = self.env['ir.attachment'].search([('folder_id', '=', False),
                                                                ('res_model', '=', 'sale.order')])
                if attachments.exists():
                    vals = {}
                    if values.get('sale_folder'):
                        vals['folder_id'] = values['sale_folder']
                    elif company.sale_folder:
                        vals['folder_id'] = company.sale_folder.id

                    if values.get('sale_tags'):
                        vals['tag_ids'] = values['sale_tags']
                    elif company.sale_tags:
                        vals['tag_ids'] = [(6, 0, company.sale_tags.ids)]
                    if len(vals):
                        attachments.write(vals)

        return super(ResCompany, self).write(values)
