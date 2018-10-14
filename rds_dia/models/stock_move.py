'''
Created on 9 Aug 2018

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
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT


class stock_picking_custom(models.Model):
    _inherit = 'stock.move'

    data_decorrenza = fields.Date(_('Data Decorrenza'))

    @api.model
    def getDiaLocation(self):
        stock_location_object = self.env['stock.location']
        diaLocation = {'name': 'DiaInventoryLocation',
                       'usage': 'inventory',
                       }
        stock_location_id = stock_location_object.search([('name', '=', diaLocation['name'])])
        if not stock_location_id:
            stock_location_id = stock_location_object.create(diaLocation)
        return stock_location_id

    @api.model
    def createDiaMove(self, product_id, qty, stock_location_id, forceDate=False):
        dia_location_id = self.getDiaLocation()
        move_import_date = datetime.now().strftime("%Y%m%d-%H%M%S")
        if forceDate:
            move_import_date = forceDate.strftime("%Y%m%d-%H%M%S")
        logging.info("Create stock move %r" % move_import_date)
        abs_qty = abs(qty)
        move_create = {'name': move_import_date,
                       'product_id': product_id.id,
                       'ordered_qty': abs_qty,
                       'product_uom_qty': abs_qty,
                       'note': 'Automatic move made from dia import',
                       'product_uom': product_id.uom_id.id}
        if qty > 0:
            move_create['location_id'] = dia_location_id.id
            move_create['location_dest_id'] = stock_location_id
        else:
            move_create['location_id'] = stock_location_id
            move_create['location_dest_id'] = dia_location_id.id
        stock_move = self.create(move_create)
        stock_move.quantity_done = abs_qty
        stock_move._action_done()

    @api.model
    def updateSaleOrderLineFromPicking(self, vals):
        errors = []
        for ddt_num, valsDictList in vals[0].items():
            for valsDict in valsDictList:
                sale_order_number = valsDict.get('sale_number', '')
                product_uom = valsDict.get('uom', 1)
                _ddtNumber = valsDict.get('num_ddt', ddt_num)
                dest_loc_id = valsDict.get('dest_loc_id', 15)
                price_unit = valsDict.get('prod_price', 0)
                prod_qty = valsDict.get('prod_qty', 0)
                
                saleBrws = self.getSaleOrder(sale_order_number)
                if not saleBrws:
                    errors.append('Sale Order not found with vals %r' % (valsDict))
                    continue
                productBrws = self.getProduct(valsDict.get('prod_code', ''))
                if not productBrws:
                    errors.append('Product not found with vals %r' % (valsDict))
                    continue
                sale_line_list = self.getSaleLine(saleBrws, productBrws, prod_qty, getAll=True)
                if not sale_line_list:
                    errors.append('Product not found with vals %r' % (valsDict))
                    continue
                #saleLineObj = self.env['sale.order.line']
                count = 1
                for lineBrws in sale_line_list:
                    newQty = lineBrws.product_uom_qty - prod_qty
                    #lineBrws.write({'product_uom_qty': newQty})
                    if lineBrws.product_uom_qty - lineBrws.qty_delivered - newQty < 0:
                        errors.append('[ERROR %r] newQty %r, delivered %r, requested %r %r' % (count, newQty, lineBrws.qty_delivered, lineBrws.product_uom_qty, valsDict))
                    else:
                        errors.append('[INFO %r] newQty %r, delivered %r, requested %r %r' % (count, newQty, lineBrws.qty_delivered, lineBrws.product_uom_qty, valsDict))
                    count += 1
        return errors
        
    @api.model
    def createDiaPickingAndMove(self, vals):
        '''
        'num_ddt': 'U0001590',
         'data_ddt': '10/08/2018',
         'prod_code': 'A284670',
         'prod_qty': 2000,
         'prod_price': 1.661,
         'sale_number': ''
        '''
        errors = []
        for ddt_num, valsDictList in vals[0].items():
            for valsDict in valsDictList:
                sale_order_number = valsDict.get('sale_number', '')
                product_uom = valsDict.get('uom', 1)
                _ddtNumber = valsDict.get('num_ddt', ddt_num)
                dest_loc_id = valsDict.get('dest_loc_id', 15)
                price_unit = valsDict.get('prod_price', 0)
                prod_qty = valsDict.get('prod_qty', 0)
                
                saleBrws = self.getSaleOrder(sale_order_number)
                if not saleBrws:
                    errors.append('Sale Order not found with vals %r' % (valsDict))
                    continue
                productBrws = self.getProduct(valsDict.get('prod_code', ''))
                if not productBrws:
                    errors.append('Product not found with vals %r' % (valsDict))
                    continue
                
                pickingTypeBrws = self.getOutPickingType()
                odooStyleDateTime = self.computeDate(valsDict.get('data_ddt', ''))
                sale_line_id = self.getSaleLine(saleBrws, productBrws, prod_qty)
                pickBrws = self.createPicking(saleBrws.partner_id.id, pickingTypeBrws.id, odooStyleDateTime, ddt_num, odooStyleDateTime, dest_loc_id)
                moveBrws = self.createMove(dest_loc_id, productBrws.id, price_unit, prod_qty, product_uom, sale_line_id, pickBrws.id, odooStyleDateTime, saleBrws.name, pickingTypeBrws.id, productBrws.name)
                
                pickBrws.action_confirm()
                pickBrws.action_done()
                moveBrws._action_confirm()
                moveBrws._action_done()
                moveBrws.date = odooStyleDateTime
                for line in moveBrws.move_line_ids:
                    line.date = odooStyleDateTime
        for error in errors:
            logging.warning(error)
        return errors

    @api.model
    def createMove(self, dest_loc_id, product_id, price_unit, qty, product_uom, sale_line_id, picking_id, refdate, origin, picking_type_id, name):
        return self.create(
            {'location_id': self.getDiaLocation().id,
             'location_dest_id': dest_loc_id,
             'product_id': product_id,
             'price_unit': price_unit,
             'product_uom_qty': qty,
             'ordered_qty': qty,
             'product_uom': product_uom,
             'quantity_done': qty,
             'sale_line_id': sale_line_id,
             'picking_id': picking_id,
             'date_expected': refdate,
             'date': refdate,
             'origin': origin,
             'picking_type_id': picking_type_id,
             'name': name,
            }
            )
        
    @api.model
    def createPicking(self, partner_id, picking_type_id, date, ddt_number, ddt_date, dest_loc_id):
        pickObj = self.env['stock.picking']
        return pickObj.create({
            'partner_id': partner_id,
            'main_partner_id': partner_id,
            'picking_type_id': picking_type_id,
            'scheduled_date': date,
            'ddt_number': ddt_number,
            'ddt_date': ddt_date,
            'location_id': dest_loc_id,
            'location_dest_id': dest_loc_id,
            })

    @api.model
    def getSaleLine(self, saleBrws, productBrws, prod_qty, getAll=False):
        saleLineObj = self.env['sale.order.line']
        res = saleLineObj.search([
            ('order_id', '=', saleBrws.id),
            ('product_id', '=', productBrws.id),
            ('product_uom_qty', '=', prod_qty),
            ])
        if not res:
            res = saleLineObj.search([
            ('order_id', '=', saleBrws.id),
            ('product_id', '=', productBrws.id),
            ])
        if res:
            if getAll:
                return res
            return res[0].id
        return False
        
    @api.model
    def getProduct(self, prodName):
        if not prodName:
            return self.env['product.product']
        prodEnv = self.env['product.product']
        return prodEnv.search([('default_code', '=', prodName)])

    @api.model
    def computeDate(self, strDate):
        newDT = datetime.strptime(strDate, "%d/%m/%Y")
        return newDT.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
    @api.model
    def getOutPickingType(self):
        pickingBrwsList = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing')
                ])
        for pickingBrws in pickingBrwsList:
            if pickingBrws.warehouse_id.code == 'RDSWH':
                return pickingBrws
        return self.env['stock.picking.type'].browse(5)
        
    @api.model
    def getSaleOrder(self, saleName):
        if not saleName:
            return self.env['sale.order']
        saleOrderObj = self.env['sale.order']
        return saleOrderObj.search([('name', '=', saleName)])
    
    @api.multi
    def clientActionAssing(self):
        for moveBrws in self:
            moveBrws._action_assign()
        return True
    
    @api.multi
    def clientActionConfirm(self):
        for moveBrws in self:
            moveBrws._action_confirm()
        return True

    @api.multi
    def clientActionDone(self):
        for moveBrws in self:
            moveBrws._action_done()
        return True
