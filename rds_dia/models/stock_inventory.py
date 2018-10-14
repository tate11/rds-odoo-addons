'''
Created on 7 Jun 2018

@author: mboscolo
'''
import os
import logging
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from io import BytesIO
from odoo.exceptions import UserError
from docutils.parsers.rst.directives import encoding


class stock_picking_custom(models.Model):
    _inherit = 'stock.inventory'
# id  | inventory_id | partner_id | product_id
# |  product_name   | product_code | product_uom_id
# | product_qty | location_id |        location_name
# | package_id | prod_lot_id | prodlot_name | company_id
# | theoretical_qty | create_uid |        create_date
# | write_uid |         write_date

#     @api.model
#     def uploadInventory(self, tupleArg):
#         stock_locationObj = self.env['stock.location']
#         objStockInventoryLine = self.env['stock.inventory.line']
#         objProductProduct = self.env['product.product']
#         inventoryName, items, default_location_id = tupleArg
#         objInventory = self.create({'name': inventoryName,
#                                     'filter': 'partial'})
#         objInventory.action_start()
#         inventory_id = objInventory.id
#         for row in items:
#             name = row.get('product_name')
#             qty = row.get('product_qty')
#             rds_location_name = row.get('rds_location_name')
#             location_id = default_location_id
#             for location in stock_locationObj.search([('dia_location', '=', rds_location_name)]):
#                 location_id = location.id
#             product_id = objProductProduct.search([('default_code', '=', name.strip())])
#             if product_id:
#                 to_create = {'product_id': product_id.id,
#                              'product_qty': qty,
#                              'inventory_id': inventory_id,
#                              'location_id': location_id}
#                 objStockInventoryLine.create(to_create)
#         return True

    @api.model
    def uploadInventory(self, tupleArg):
        out_err = []
        stock_locationObj = self.env['stock.location']
        stock_move_obj = self.env['stock.move']
        objProductProduct = self.env['product.product']
        _inventoryName, items, default_location_id = tupleArg
        for row in items:
            try:
                name = row.get('product_name')
                qty = row.get('product_qty')
                rds_location_name = row.get('rds_location_name')
                location_id = default_location_id
                for location in stock_locationObj.search([('dia_location', '=', rds_location_name)]):
                    location_id = location.id
                    break
                product_id = objProductProduct.search([('default_code', '=', name.strip())])
                if not product_id:
                    out_err.append("Unable to find product from row %r" % row)
                    continue
                stock_move_obj.createDiaMove(product_id, qty, location_id)
            except Exception as ex:
                out_err.append("Row: %r Err: %r" % (row, ex))
        return out_err
