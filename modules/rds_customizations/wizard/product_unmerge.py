# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval
import functools
import itertools
import logging
import psycopg2

from odoo import api, fields, models
from odoo import SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import mute_logger

_logger = logging.getLogger('base.product.merge')

class ProductTemplate(models.TransientModel):
    _inherit = 'product.template'

    def _unpack(self):
        for t in self:
            for v in t.product_variant_ids:
                v.split()
            t.unlink()

class ProductProduct(models.TransientModel):
    _inherit = 'product.product'

    def _shared_table(self):
        return [
            ['mrp_bom', 'product_id', 'product_tmpl_id'],
            ['product_customerinfo', 'product_id', 'product_tmpl_id'],
            ['product_pricelist_item', 'product_id', 'product_tmpl_id'],
            ['product_replenish', 'product_id', 'product_tmpl_id'],
            ['product_supplierinfo', 'product_id', 'product_tmpl_id'],
            ['quality_alert', 'product_id', 'product_tmpl_id'],
            ['quality_point', 'product_id', 'product_tmpl_id'],
            ['stock_change_product_qty', 'product_id', 'product_tmpl_id'],
            ['stock_rules_report', 'product_id', 'product_tmpl_id'],
            ['product_product', 'id', 'product_tmpl_id']
        ]

    def _clear_tables(self):
        return [
            ['product_attribute_value_product_product_rel', 'product_product_id']
        ]

    @api.model
    def split(self):
        """ Update all foreign key from the src_partner to dst_partner. All many2one fields will be updated.
            :param src_partners : merge source res.partner recordset (does not include destination one)
            :param dst_partner : record of destination res.partner
        """

        _template = self.self.product_tmpl_id.with_context(create_product_product=True)
        template = _template.copy()

        relations = self._shared_table()
        clear_relations = self._clear_tables()

        for table, column, column2 in relations:
            query_dic = {
                'table': table,
                'column': column,
                'column_t': column2
            }

            try:
                with mute_logger('odoo.sql_db'), self._cr.savepoint():
                    query = 'UPDATE "%(table)s" SET %(column_t)s = %%s WHERE %(column)s=%%s' % query_dic
                    self._cr.execute(query, (template.id, self.id,))
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent partner_id is useless, better delete it
                query = 'DELETE FROM "%(table)s" WHERE "%(column)s"=%%s' % query_dic
                self._cr.execute(query, (self.id,))

        for table, column in clear_relations:
            query_dic = {
                'table': table,
                'column': column
            }

            query = 'DELETE FROM "%(table)s" WHERE "%(column)s"=%%s' % query_dic
            self._cr.execute(query, (self.id,))