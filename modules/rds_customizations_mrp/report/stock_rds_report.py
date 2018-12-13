# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class StockAdvReport(models.Model):
    _name = "stock.rds.report"
    _description = "Stock Report"
    _auto = False
    _rec_name = 'date_excepted'
    _order = 'date_excepted desc'

    location_id = fields.Many2one("stock.location", "Locazione")
    product_tmpl_id = fields.Many2one('product.template', "Modello Prodotto")
    product_id = fields.Many2one('product.product', "Prodotto")
    date_excepted = fields.Datetime('Data')
    state = fields.Selection([
        ('remaining', 'Giacenza'),
        ('waiting', 'In Attesa altro mov.'),
        ('confirmed', 'In attesa di materiale'),
        ('partially_available', 'Parzialmente Disp.'),
        ('assigned', 'A Disposizione')
        ], 'Stato')
    qty = fields.Float("Quantità")

    def _query(self, with_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            min(x.product_id) as id,
            x.location_id as location_id,
            x.product_tmpl_id as product_tmpl_id,
            x.product_id as product_id,
            x.date_excepted as date_excepted,
            x.state as state,
            sum(x.qty) as qty
        """

        from_ = """
                (
                    SELECT 
                        loc.id location_id,
                        move.product_id product_id,
                        prodt.id as product_tmpl_id,
                        move.date_excepted as date_excepted,
                        move.state state,
                        (move.product_uom_qty / u.factor * u2.factor) as qty
                    FROM stock_location loc 
                    LEFT JOIN stock_move move ON move.location_dest_id = loc.id
                    LEFT JOIN product_product prod ON prod.id = move.product_id
                    LEFT JOIN product_template prodt ON prodt.id = prod.product_tmpl_id
                    LEFT JOIN uom_uom u ON (u.id=move.product_uom)
                    LEFT JOIN uom_uom u2 ON (u2.id=prodt.uom_id)
                    WHERE move.state in ('assigned', 'partially_available', 'confirmed', 'waiting')
                    UNION ALL

                    SELECT
                        loc.id location_id,
                        move.product_id product_id,
                        prodt.id as product_tmpl_id,
                        move.date_excepted as date_excepted,
                        move.state state,
                        -(move.product_uom_qty / u.factor * u2.factor) as qty
                    FROM stock_location loc
                    LEFT JOIN stock_move move ON move.location_dest_id = loc.id
                    LEFT JOIN product_product prod ON prod.id = move.product_id
                    LEFT JOIN product_template prodt ON prodt.id = prod.product_tmpl_id
                    LEFT JOIN uom_uom u ON (u.id=move.product_uom)
                    LEFT JOIN uom_uom u2 ON (u2.id=prodt.uom_id)
                    WHERE move.state in ('assigned', 'partially_available', 'confirmed', 'waiting')
                    UNION ALL

                    SELECT
                        quant.location_id location_id,
                        quant.product_id product_id,
                        prodt.id as product_tmpl_id,
                        NOW() as date_excepted,
                        'remaining' as state,
                        quant.quantity as qty
                    FROM stock_quant quant
                    LEFT JOIN product_product prod ON prod.id = quant.product_id
                    LEFT JOIN product_template prodt ON prodt.id = prod.product_tmpl_id
                ) x
        """

        groupby_ = """
            x.location_id,
            x.product_tmpl_id,
            x.product_id,
            x.date_excepted,
            x.state
        """

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))