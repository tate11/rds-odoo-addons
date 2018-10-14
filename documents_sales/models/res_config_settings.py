# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_default_sale_folder(self):
        folder_id = self.env.user.company_id.sale_folder
        if folder_id.exists():
            return folder_id
        return False

    dms_sale_settings = fields.Boolean(related='company_id.dms_sale_settings', readonly=False,
                                          default=lambda self: self.env.user.company_id.dms_sale_settings,
                                          string="Sale Folder")
    sale_folder = fields.Many2one('documents.folder', related='company_id.sale_folder', readonly=False,
                                     default=_get_default_sale_folder,
                                     string="sale default folder")
    sale_tags = fields.Many2many('documents.tag', 'sale_tags_table',
                                    related='company_id.sale_tags',
                                    readonly=False,
                                    default=lambda self: self.env.user.company_id.sale_tags.ids,
                                    string="Sale Tags")

