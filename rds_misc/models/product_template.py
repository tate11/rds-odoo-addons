# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductTemplate(models.Model):

    _inherit = ['product.template']


    default_vendor = fields.Many2one('res.partner', string='Fornitore Principale')
    default_location = fields.Many2one('stock.location', string='Locazione Predefinita')

    def get_earliest_code(self):
        cat = self.categ_id

        while (not cat.has_code) and bool(cat.parent_id):
            cat = cat.parent_id

        return cat.code_prefix, cat.code_suffix, cat.code_body_len

    def action_get_code(self):
        pfx, sfx, clen = self.get_earliest_code()
        pfx = str(pfx) if pfx else ''
        sfx = sfx if sfx else ''
        clen = clen if clen else 5

        code_family = self.env['product.template'].search([('default_code', '=', (pfx+'%'))]).sorted(key=lambda p: p.default_code)
        if code_family:
            last_code = code_family[0].default_code if code_family[0].default_code else (pfx + ''.zfill(clen) + sfx) 
        else:
            last_code = pfx + ''.zfill(clen) + sfx

        lw_code_body = int((last_code[-(len(sfx)+clen):])[:clen])
        tentative_code = pfx + str(lw_code_body).zfill(clen) + sfx

        while self.env['product.template'].search_count(['&', ('id', '!=', self.ids[0]), ('default_code', '=', tentative_code)]) >= 1:
            lw_code_body += 1
            tentative_code = pfx + str(lw_code_body).zfill(clen) + sfx
        
        self.default_code = tentative_code

    _sql_constraints = [('default_code_uniq', 'unique(default_code)', 'Il codice deve essere unico!')]



class ProductCategory(models.Model):

    _inherit = ['product.category']


    has_code = fields.Boolean(string="Codice per Categoria", default=False)
    code_prefix = fields.Char(string="Prefisso Codice Prodotto")
    code_suffix = fields.Char(string="Suffisso Codice Prodotto")
    code_body_len = fields.Integer(string="Lunghezza Codice", default=5)