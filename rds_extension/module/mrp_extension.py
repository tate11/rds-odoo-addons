# -*- coding: utf-8 -*-

'''
Created on Jun 5, 2018

@author: daniel
'''
from odoo import api, models, fields, _
from odoo import SUPERUSER_ID

class ManufacturingReporting(models.Model):
    _name = "mrp.production_pivot_rds_view"
    _auto = False

    product_id = fields.Many2one(comodel_name='product.product', string=_('Product'))
    stock_quant = fields.Float(string=_('Location Stock Quantity'))
    location_id = fields.Many2one(comodel_name='stock.location', string=_('Location'))
    sale_order_id = fields.Many2one(comodel_name='sale.order', string=_('Sale Order'))
    product_uom_qty = fields.Float(string=_('Ordered Quantity'))
    qty_delivered = fields.Float(string=_('Delivered Quantity'))
    state = fields.Char(string=_('Status'))
    requested_date = fields.Datetime(string=_('Requested Date'))

    def __init__(self, pool, cr):
        """ Deprecated method to initialise the model. """
        cr.execute("""drop view if exists mrp_production_pivot_rds_view_start cascade;""")
        cr.execute("""drop view if exists mrp_production_pivot_rds_view cascade;""")
        cr.execute(
            '''
create or replace view mrp_production_pivot_rds_view_start as
select
    quant.product_id product_id,
    quant.quantity stock_quant,
    quant.location_id location_id,
    order_id sale_order_id,
    sale.state state,
    sale.product_uom_qty product_uom_qty,
    sale.qty_delivered qty_delivered,
    sale.requested_date requested_date
from sale_order_line sale
left join product_product product on product.id=sale.product_id
left join mrp_bom as bom on bom.product_tmpl_id=product.product_tmpl_id
left join mrp_bom_line bom_line on bom_line.bom_id = bom.id
left join stock_quant quant on  quant.product_id=sale.product_id or quant.product_id = bom_line.product_id
order by sale.product_id
            ''')
        cr.execute('''
create or replace view mrp_production_pivot_rds_view as
select row_number() over (order by product_id) id, mrp_production_pivot_rds_view_start.*
from mrp_production_pivot_rds_view_start
        ''')
