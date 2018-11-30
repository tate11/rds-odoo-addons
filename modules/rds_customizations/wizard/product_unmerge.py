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

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _unpack(self, attribute_id=False):
        for t in self:
            if t.product_variant_count <= 1:
                continue

            if len(t.attribute_line_ids.filtered(lambda x: x.attribute_id.id != attribute_id)) == len(t.attribute_line_ids):
                continue

            attr = t.attribute_line_ids.filtered(lambda x: x.attribute_id.id == attribute_id)

            if not attr:
                for v in t.product_variant_ids:
                    _template = self.with_context(create_product_product=True)
                    template = _template.copy()
                    v.split(template)

            else:
                for value in attr.value_ids:
                    _template = self.with_context(create_product_product=True)
                    template = _template.copy({'name': self.name + "{}".format(value.name)})

                    for att_line in t.attribute_line_ids.filtered(lambda x: x.attribute_id.id != attribute_id):
                        att_line.copy({'product_tmpl_id': template.id})
                    for seller_id in t.seller_ids.filtered(lambda x: x.product_id == False):
                        seller_id.copy({'product_tmpl_id': template.id})
                    for customers_id in t.customers_ids.filtered(lambda x: x.product_id == False):
                        customers_id.copy({'product_tmpl_id': template.id})

                    for v in t.product_variant_ids.filtered(lambda x: value in x.attribute_value_ids):
                        v.split(template, value)

            t.unlink()

class ProductProduct(models.Model):
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

    @api.model
    def split(self, template, clear_attribute_value=False):
        relations = self._shared_table()

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

        if clear_attribute_value:
            query = 'DELETE FROM product_attribute_value_product_product_rel WHERE product_attribute_value_id=%s AND product_product_id=%s' % (clear_attribute_value.id, self.id)
            self._cr.execute(query, ())