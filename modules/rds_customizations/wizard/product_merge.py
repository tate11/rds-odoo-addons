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

class MergePartnerAutomatic(models.TransientModel):
    """
        The idea behind this wizard is to create a list of potential partners to
        merge. We use two objects, the first one is the wizard for the end-user.
        And the second will contain the partner list to merge.
    """

    _name = 'base.product.merge.automatic.wizard'
    _description = 'Merge Partner Wizard'

    state = fields.Selection([
        ('selection', 'Selection'),
        ('finished', 'Finished')
    ], readonly=True, required=True, string='State', default='selection')

    product_ids = fields.Many2many('product.product', string="Products")

    src_product_id = fields.Many2one('product.product', string='Source Product')
    dst_product_id = fields.Many2one('product.product', string='Destination Product')


    # ----------------------------------------
    # Update method. Core methods to merge steps
    # ----------------------------------------

    def _get_fk_on(self, table):
        """ return a list of many2one relation with the given table.
            :param table : the name of the sql table to return relations
            :returns a list of tuple 'table name', 'column name'.
        """
        query = """
            SELECT cl1.relname as table, att1.attname as column
            FROM pg_constraint as con, pg_class as cl1, pg_class as cl2, pg_attribute as att1, pg_attribute as att2
            WHERE con.conrelid = cl1.oid
                AND con.confrelid = cl2.oid
                AND array_lower(con.conkey, 1) = 1
                AND con.conkey[1] = att1.attnum
                AND att1.attrelid = cl1.oid
                AND cl2.relname = %s
                AND att2.attname = 'id'
                AND array_lower(con.confkey, 1) = 1
                AND con.confkey[1] = att2.attnum
                AND att2.attrelid = cl2.oid
                AND con.contype = 'f'
        """
        self._cr.execute(query, (table,))
        return self._cr.fetchall()

    @api.model
    def _update_foreign_keys(self, src_product, dst_product):
        """ Update all foreign key from the src_partner to dst_partner. All many2one fields will be updated.
            :param src_partners : merge source res.partner recordset (does not include destination one)
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_foreign_keys for dst_product: %s for src_product: %s', dst_product.id, str(src_product.id))

        # find the many2one relation to a partner
        Product = self.env['product.product']
        ProductTemplate = self.env['product.template']

        relations = self._get_fk_on('product_product')
        tmpl_relations = self._get_fk_on('product_template')

        for table, column in tmpl_relations:
            if 'base_product_merge_' in table:  # ignore two tables
                continue

            # get list of columns of current table (exept the current fk column)
            query = "SELECT column_name FROM information_schema.columns WHERE table_name LIKE '%s'" % (table)
            self._cr.execute(query, ())
            columns = []
            for data in self._cr.fetchall():
                if data[0] != column:
                    columns.append(data[0])

            # do the update for the current table/column in SQL
            query_dic = {
                'table': table,
                'column': column,
                'value': columns[0],
            }
            if len(columns) <= 1:
                # unique key treated
                query = """
                    UPDATE "%(table)s" as ___tu
                    SET %(column)s = %%s
                    WHERE
                        %(column)s = %%s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                %(column)s = %%s AND
                                ___tu.%(value)s = ___tw.%(value)s
                        )""" % query_dic
                self._cr.execute(query, (dst_product.product_tmpl_id.id, src_product.product_tmpl_id.id, dst_product.product_tmpl_id.id))
            else:
                try:
                    with mute_logger('odoo.sql_db'), self._cr.savepoint():
                        query = 'UPDATE "%(table)s" SET %(column)s = %%s WHERE %(column)s=%%s' % query_dic
                        self._cr.execute(query, (dst_product.product_tmpl_id.id, src_product.product_tmpl_id.id,))

                        '''
                        # handle the recursivity with parent relation
                        if column == Partner._parent_name and table == 'res_partner':
                            query = """
                                WITH RECURSIVE cycle(id, parent_id) AS (
                                        SELECT id, parent_id FROM res_partner
                                    UNION
                                        SELECT  cycle.id, res_partner.parent_id
                                        FROM    res_partner, cycle
                                        WHERE   res_partner.id = cycle.parent_id AND
                                                cycle.id != cycle.parent_id
                                )
                                SELECT id FROM cycle WHERE id = parent_id AND id = %s
                            """
                            self._cr.execute(query, (dst_partner.id,))
                            # NOTE JEM : shouldn't we fetch the data ?'''
                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record with nonexistent partner_id is useless, better delete it
                    query = 'DELETE FROM "%(table)s" WHERE "%(column)s"=%%s' % query_dic
                    self._cr.execute(query, (src_product.product_tmpl_id.id,))

        for table, column in relations:
            if 'base_product_merge_' in table:  # ignore two tables
                continue

            # get list of columns of current table (exept the current fk column)
            query = "SELECT column_name FROM information_schema.columns WHERE table_name LIKE '%s'" % (table)
            self._cr.execute(query, ())
            columns = []
            for data in self._cr.fetchall():
                if data[0] != column:
                    columns.append(data[0])

            # do the update for the current table/column in SQL
            query_dic = {
                'table': table,
                'column': column,
                'value': columns[0],
            }
            if len(columns) <= 1:
                # unique key treated
                query = """
                    UPDATE "%(table)s" as ___tu
                    SET %(column)s = %%s
                    WHERE
                        %(column)s = %%s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                %(column)s = %%s AND
                                ___tu.%(value)s = ___tw.%(value)s
                        )""" % query_dic
                self._cr.execute(query, (dst_product.id, src_product.id, dst_product.id))
            else:
                try:
                    with mute_logger('odoo.sql_db'), self._cr.savepoint():
                        query = 'UPDATE "%(table)s" SET %(column)s = %%s WHERE %(column)s=%%s' % query_dic
                        self._cr.execute(query, (dst_product.id, src_product.id,))

                        '''
                        # handle the recursivity with parent relation
                        if column == Partner._parent_name and table == 'res_partner':
                            query = """
                                WITH RECURSIVE cycle(id, parent_id) AS (
                                        SELECT id, parent_id FROM res_partner
                                    UNION
                                        SELECT  cycle.id, res_partner.parent_id
                                        FROM    res_partner, cycle
                                        WHERE   res_partner.id = cycle.parent_id AND
                                                cycle.id != cycle.parent_id
                                )
                                SELECT id FROM cycle WHERE id = parent_id AND id = %s
                            """
                            self._cr.execute(query, (dst_partner.id,))
                            # NOTE JEM : shouldn't we fetch the data ?'''
                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record with nonexistent partner_id is useless, better delete it
                    query = 'DELETE FROM "%(table)s" WHERE "%(column)s"=%%s' % query_dic
                    self._cr.execute(query, (src_product.id,))

    @api.model
    def _update_reference_fields(self, src_product, dst_product, model='product.product'):
        """ Update all reference fields from the src_partner to dst_partner.
            :param src_partners : merge source res.partner recordset (does not include destination one)
            :param dst_partner : record of destination res.partner
        """
        _logger.debug('_update_reference_fields for dst_partner: %s for src_partners: %r', dst_product.id, src_product.id)

        def update_records(model, src, field_model='model', field_id='res_id'):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search([(field_model, '=', model), (field_id, '=', src.id)])
            try:
                with mute_logger('odoo.sql_db'), self._cr.savepoint():
                    return records.sudo().write({field_id: dst_product.id})
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent partner_id is useless, better delete it
                return records.sudo().unlink()

        update_records = functools.partial(update_records)

        update_records('calendar', src=dst_product, field_model='model_id.model')
        update_records('ir.attachment', src=dst_product, field_model='res_model')
        update_records('mail.followers', src=dst_product, field_model='res_model')
        update_records('mail.message', src=dst_product)
        update_records('ir.model.data', src=dst_product)

        records = self.env['ir.model.fields'].search([('ttype', '=', 'reference')])
        for record in records.sudo():
            try:
                Model = self.env[record.model]
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue

            if field.compute is not None:
                continue

            records_ref = Model.sudo().search([(record.name, '=', '%s,%d' % (model, src_product.id))])
            values = {
                record.name: '%s,%d' % (model, src_product.id),
            }
            records_ref.sudo().write(values)



    def _merge(self, src_product, dst_product):
        """ private implementation of merge partner
            :param partner_ids : ids of partner to merge
            :param dst_partner : record of destination res.partner
            :param extra_checks: pass False to bypass extra sanity check (e.g. email address)
        """
        # super-admin can be used to bypass extra checks

        Product = self.env['product.product']

        if src_product.product_tmpl_id.product_variant_count != 1:
            raise ValidationError("Il prodotto di origine deve essere senza varianti!")

        for i in src_product.item_ids:
            i.product_id = src_product
        
        for i in src_product.customer_ids:
            i.product_id = src_product

        for i in src_product.seller_ids:
            i.product_id = src_product
            
        for i in src_product.bom_ids:
            i.product_id = src_product

        # call sub methods to do the merge
        self._update_foreign_keys(src_product, dst_product)
        self._update_reference_fields(src_product, dst_product)
        self._update_reference_fields(src_product.product_tmpl_id, dst_product.product_tmpl_id)

        # delete source partner, since they are merged
        src_product.product_tmpl_id.unlink()
        src_product.unlink()


    #ACTIONS

    @api.multi
    def action_merge(self):
        """ Merge Contact button. Merge the selected partners, and redirect to
            the end screen (since there is no other wizard line to process.
        """
        if not self.dst_product_id or not self.src_product_id:
            self.write({'state': 'finished'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        
        self.product_ids.check_access_rights('unlink')
        self._merge(self.src_product_id, self.dst_product_id)


    @api.model
    def product_make_merge(self, records):
        a = self.create({'product_ids': [(4, x) for x in records.ids]})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': a.id,
            'view_mode': 'form',
            'target': 'new',
        }
