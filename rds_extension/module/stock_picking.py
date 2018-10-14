##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 27/set/2016 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 27/set/2016

@author: mboscolo
'''
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
import tempfile
import base64
import csv
import os


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def _getMainPartner(self):
        for stock_picking_id in self:
            for move in stock_picking_id.move_lines:
                if move.sale_line_id:
                    stock_picking_id.main_partner_id = move.sale_line_id.order_partner_id
                break
            if not stock_picking_id.main_partner_id:
                stock_picking_id.main_partner_id = stock_picking_id.partner_id

    main_partner_id = fields.Many2one('res.partner', compute='_getMainPartner')
    weight_ddt = fields.Float("Peso Reale")
    check_bvit_price = fields.Boolean(_("Verifica Prezzo DDT acquisto"))

    @api.multi
    def checkBbvitPrice(self):
        outDict = {}
        outDict['check_bvit_price'] = False
        for pickBrws in self:
            if pickBrws.causale_dia and pickBrws.causale_dia.name in ['BVIT', 'BVCE'] and pickBrws.causale_dia.push_to_dia:
                for lineBrws in pickBrws.move_lines:
                    if not lineBrws.sale_line_id:
                        outDict['check_bvit_price'] = True
                    elif not lineBrws.sale_line_id.price_unit:
                        outDict['check_bvit_price'] = True
        return outDict

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        if not res:
            return res
        vals2 = self.checkBbvitPrice()
        res.write(vals2)
        return res

    @api.multi
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if not res:
            return res
        vals2 = self.checkBbvitPrice()
        return super(StockPicking, self).write(vals2)

    @api.one
    @api.depends('package_ids', 'weight_bulk')
    def _compute_shipping_weight(self):
        res = super(StockPicking, self)._compute_shipping_weight()
        self.weight_ddt = self.shipping_weight
        return res

    @api.multi
    def getDDTLines(self):
        outDict = {}
        for pickingBrws in self:
            for pickingLineBrws in pickingBrws.move_lines:
                accAnAccBrws = self.env['account.analytic.account'].browse()
                orderBrws = pickingLineBrws.sale_line_id.order_id
                if orderBrws:
                    accAnAccBrws = orderBrws.analytic_account_id
                if accAnAccBrws not in outDict:
                    outDict[accAnAccBrws] = []
                outDict[accAnAccBrws].append(pickingLineBrws)
        return outDict


class RawMovesWizard(models.TransientModel):
    _name = "raw.picking_list"

    file_name = fields.Char('File Name', default='raw_export.csv')
    file_to_download = fields.Binary(string="Download")
    separator = fields.Char('Separator', default='@')
    delimiter = fields.Char('Delimiter', default='|')

    @api.multi
    def computeExportRaw(self):
        pickObj = self.env['stock.picking']
        pickingIds = self.env.context.get('active_ids', [])
        outFile = os.path.join(tempfile.gettempdir(), '%s.csv' % (self.file_name))
        fileObj = open(outFile, 'w', newline='')
        spamwriter = csv.writer(fileObj,
                                delimiter=self.delimiter,
                                quotechar=self.separator,
                                quoting=csv.QUOTE_MINIMAL)
        spamwriter.writerow(['Pick', 'DDT Name', 'Data DDT', 'Quantità'])
        for pickBrws in pickObj.browse(pickingIds):
            valsLine = []
            for moveBrws in pickBrws.move_lines:
                if moveBrws.product_id.default_code.startswith('A'):
                    valsLine = [pickBrws.name, pickBrws.ddt_number, pickBrws.scheduled_date, moveBrws.getRawTotalPlusWastage()]
                    spamwriter.writerow(valsLine)
        fileObj.close()

        with open(outFile, 'rb') as f:
            fileContent = f.read()
            if fileContent:
                self.file_to_download = base64.encodestring(fileContent)
        return {
            #  Uncomment this, comment res_id and set view_mode = tree,form to wiew in tree mode
            #  'domain': [('id', 'in', [schedaId])],
            'name': 'Grezzi',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'raw.picking_list',
            'type': 'ir.actions.act_window'}
