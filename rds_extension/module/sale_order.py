'''
Created on 20 Jun 2018

@author: mboscolo
'''
import copy
from odoo import api
from odoo import fields
from odoo import models

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_compare
from datetime import datetime, timedelta, time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class DataExportTable(object):
    def __init__(self):
        self. _rows = []
        self._headers = []

    def addRow(self, valueDict, toExclude=[]):
        for k in valueDict.keys():
            if k not in self._headers and k not in toExclude:
                self._headers.append(k)
        self._rows.append(valueDict)

    @property
    def orderedHeaders(self):
        out = (
               #('ORDER_NAME', 'Ordine'),
               ('CUSTOMER', 'Cliente'),
               #('DATE', 'DAta Consegna'),
               ('MAIN_PRODUCT', 'Codice'),
               ('REFE', 'Codice E'),
               ('DES', 'Descrizione'),
#                ('QTY_REQUIRED', 'Qty Richiesta'),
#                ('QTY_DELIVERED', 'Qty Consegnata'),
#                ('QTY_MISSED', 'Qty Mancante'),
               ('MOLD', 'Stampo'))
        indexheader = [i[0] for i in out]
        locations = []
        for item in self._headers:
            if item not in indexheader:
                locations.append((item, item))
        return out + tuple(locations)

    def createCsv(self):
        out = []
        row = ""
        for indexVal in self.orderedHeaders:
            row += indexVal[1] + ";"
        out.append(row)
        for line in self._rows:
            row = ""
            for indexVal in self.orderedHeaders:
                row += str(line.get(indexVal[0], '')) + ";"
            out.append(row)
        return "\n".join(out)

    def htmlTable(self):
        headers = self.orderedHeaders
        out = "<table><thead><tr>"
        for indexVal in headers:
            out += "<th>%s</th>" % indexVal[1]
        out += "</tr></thead><tbody>"
        for line in self._rows:
            if self._rows.index(line) % 2 == 0:
                out += '<tr style="background-color: #edeff2;color: black;">'
            else:
                out += '<tr style="background-color: #a7a8aa;color: black;">'
            for indexVal in headers:
                out += "<td margin: 15px;>%s</td>" % line.get(indexVal[0], '')
            out += "</tr>"
        out += "</tbody></table>"
        return out


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def getLocations(self):
        """
        get all the supplier locations
        """
        return self.env['stock.location'].search('usage', '=', 'supplier').ids

    def getSaleOrderStateName(self, sale_order_state):
        if sale_order_state == 'sale':
            return 'O'
        elif sale_order_state in ['draft', 'valid', 'sent']:
            return 'P'

    @api.model
    def preComputeLines(self, saleOrders):
        headers = []
        outDict = {}
        for saleOrderBrws in saleOrders:
            saleOrderState = saleOrderBrws.state
            for line_id in saleOrderBrws.order_line:
                product_id = line_id.product_id
                if product_id.default_code and product_id.default_code[0] == "A":
                    outDict.setdefault(product_id, {})                              # Product
                    partner = line_id.order_id.partner_id
                    outDict[product_id].setdefault(partner, {})                     # Partner
                    deliveryDate = line_id.delivery_date
                    header = self.computeHeader(saleOrderState, deliveryDate)
                    val = outDict[product_id][partner].setdefault(header, 0)        # Order State
                    qty = line_id.product_uom_qty - line_id.qty_delivered
                    if val:
                        outDict[product_id][partner][header] += int(qty)
                    else:
                        outDict[product_id][partner][header] = int(qty)
                    if header not in headers:
                        headers.append(header)
        headers.sort()
        return outDict, headers

    def computeHeader(self, saleOrderState, deliveryDateStr):
        deliveryDate = ''
        deliveryMonth = ''
        deliveryYear = ''
        if deliveryDateStr:
            deliveryDate = datetime.strptime(deliveryDateStr, DEFAULT_SERVER_DATETIME_FORMAT)
            deliveryMonth = str(deliveryDate.month).zfill(2)
            deliveryYear = deliveryDate.year
        return '%s-%s/%s' % (self.getSaleOrderStateName(saleOrderState), deliveryYear, deliveryMonth)

    def getHeaderAmount(self, preComputeDict, product_id, partner_id, header):
        prodDict = preComputeDict.get(product_id, {})
        partnerDict = prodDict.get(partner_id, {})
        return partnerDict.get(header, 0)

    @api.model
    def getReportQtyWhere(self):
        """
        get the report from the sale to production
        """
        outObject = self.generateData()
        return outObject.htmlTable()

    @api.model
    def getQtyProduced(self, productionBrws):
        outQty = 0
        prodId = productionBrws.product_id.id
        for moveLineBrws in productionBrws.finished_move_line_ids:
            if moveLineBrws.product_id.id == prodId:
                outQty += moveLineBrws.qty_done
        return outQty

    def getDTFromString(self, strDateTime):
        return datetime.strptime(strDateTime, DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def computeECodeQty(self, tmp_out):
        eCode = tmp_out.get('REFE', '')
        prodBrws = self.env['product.product'].search([('default_code', '=', eCode)])
        foundProduction = ""
        if prodBrws:
            productionBrwsList = self.env['mrp.production'].search([('product_id', '=', prodBrws.id)])
            for productionBrws in productionBrwsList:
                if productionBrws.state in ['planned', 'progress']:
                    to_produce = productionBrws.product_qty
                    date_start = self.getDTFromString(productionBrws.date_planned_start)
                    date_stop = self.getDTFromString(productionBrws.def_date_planned_finished)
                    n_order = productionBrws.name
                    qty_produced = self.getQtyProduced(productionBrws)
                    qty_remaining = to_produce - qty_produced
                    foundProduction += "%s_%s-%s_%s  --  " % (n_order, date_start.date(), date_stop.date(), int(qty_remaining))
        return foundProduction

    @api.model
    def generateData(self):
        keysList = []
        outObject = DataExportTable()
        saleOrders = self.search([])
        preComputeDict, headers = self.preComputeLines(saleOrders)
        for sale_order in saleOrders:
            for line_id in sale_order.order_line:
                product_id = line_id.product_id
                if product_id.default_code:
                    if product_id.default_code[0] == "A":
                        key = '%s-%s' % (product_id.id, line_id.order_id.partner_id.id)
                        if key in keysList:
                            continue
                        keysList.append(key)
                        tmp_out = line_id.getBomProductsQty()
                        for tmpQtyDict in tmp_out:
                            tmpQtyDict['MAIN_PRODUCT'] = product_id.default_code
                            tmpQtyDict['CUSTOMER'] = line_id.order_id.partner_id.name
                            tmpQtyDict['QTY_E_CODE'] = self.computeECodeQty(tmpQtyDict)
                            tmpQtyDict['Stock A code'] = self.getProductAQty(line_id.product_id)
                            for header in headers:
                                tmpQtyDict[header] = self.getHeaderAmount(preComputeDict, product_id, line_id.order_id.partner_id, header)
                            outObject.addRow(tmpQtyDict, headers)
        for header in headers:
            outObject._headers.append(header)
        return outObject

    @api.model
    def getProductAQty(self, prodBrws):
        outQty = 0
        for stock_quant in self.env['stock.quant'].search([('product_id', '=', prodBrws.id)]):
            key = stock_quant.location_id.name
            if key.upper() == 'STOCK':
                outQty += int(stock_quant.quantity)
        return outQty


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def getBomProductsQty(self):
        """
        get product qty for locations
        """
        tmpOut = {}
        tmpl_stock = self.env['stock.quant']

        def update_stock_quant(product_id, tmpOut):
            for stock_quant in tmpl_stock.search([('product_id', '=', product_id.id)]):
                key = stock_quant.location_id.name
                if key in tmpOut:
                    tmpOut[key] += int(stock_quant.quantity)
                else:
                    tmpOut[key] = int(stock_quant.quantity)

        def addEInfos(default_code_name, bom_line_id, eCodes):
            tmpEdict = {'REFE': default_code_name,
                        'DES': bom_line_id.product_id.name,
                        'MOLD': ''}
            if not eCodes:
                eCodes.append(tmpEdict)
            else:
                found = False
                for eDict in eCodes:
                    if eDict['REFE'] == default_code_name:
                        found = True
                        break
                if not found:
                    eCodes.append(tmpEdict)
            return eCodes

        def addMold(bom_id, eCode, eCodes):
            moldStr = " ".join(bom_id.sudo().tool_ids.mapped(lambda x: x.serial_no or ""))
            for eDict in eCodes:
                if eDict['REFE'] == eCode:
                    eDict['MOLD'] = moldStr

        def calculate(product_id, parent_isE=False, eCodes=[]):
            for bom_id in product_id.bom_ids:
                for bom_line_id in bom_id.bom_line_ids:
                    product_id = bom_line_id.product_id
                    default_code_name = product_id.default_code
                    if parent_isE:
                        addMold(bom_id, parent_isE, eCodes)
                    parent_isE = False
                    if default_code_name:
                        if default_code_name[0] == 'E':
                            eCodes = addEInfos(default_code_name, bom_line_id, eCodes)
                            parent_isE = default_code_name
                    if default_code_name[0] in ['A', 'B', 'C', 'D', 'E', 'F']:
                        update_stock_quant(product_id, tmpOut)
                        calculate(product_id, parent_isE, eCodes)
            return eCodes

        update_stock_quant(self.product_id, tmpOut)
        eCodes = calculate(self.product_id)

        out = []
        for eList in eCodes:
            newAList = copy.deepcopy(tmpOut)
            newAList.update(eList)
            out.append(newAList)
        if not out:
            out = [tmpOut]
        return out
