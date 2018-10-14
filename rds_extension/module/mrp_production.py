'''
Created on 12 Jul 2018

@author: mboscolo
'''

from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
import base64


def emptyCaharIfFalse(value):
    if not isinstance(value, bool):
        return value
    return ''


class OdpWizard(models.TransientModel):
    _name = 'odp_wizard_export'
    
    datas = fields.Binary(string=_('File'))
    datas_fname = fields.Char(_('File Name'))


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    note = fields.Text(string=_('Note'))

    @api.model
    def getODPWizard(self, productionIds):
        """
        get default action wizard
        """
        objNew = self.env['odp_wizard_export'].create({'datas_fname': 'ODP_completo.pdf'})
        report_production = self.env['report.rds_extension.mrp_production_multi_pdf']
        pdfContent = report_production.render_qweb_pdf(self.browse(productionIds))
        objNew.write({'datas': pdfContent})
        action = {'name': 'Post Production',
                  'view_type': 'form',
                  'view_mode': 'form',
                  'target': 'new',
                  'res_id': objNew.id,
                  'res_model': 'odp_wizard_export',
                  'type': 'ir.actions.act_window'}
        return action
        
    @api.model
    def getAllReportPdf(self):
        out_stream = []
        report_production = self.env.ref('rds_extension.report_mrp_production_report_user_call')
        out_stream.append(report_production.render_qweb_pdf([self.id]))
        routing_id = self.routing_id
        if self.mold_routing_id:
            routing_id = self.mold_routing_id
        for operation_id in routing_id.operation_ids:
            if operation_id.worksheet:
                out_stream.append(base64.b64decode(operation_id.worksheet))
        return out_stream

    @api.model
    def getRowMaterialSum(self):
        out = {}
        for production_id in self:
            for move in production_id.move_raw_ids:
                if move.state not in ['cancelled']:
                    product_id = move.product_id
                    if product_id not in out:
                        out[move.product_id] = (product_id.display_name,
                                                move.product_uom.display_name,
                                                move.product_uom_qty)
                    else:
                        name, name1, qty = out[move.product_id]
                        out[move.product_id] = (name,
                                                name1,
                                                qty + move.product_uom_qty)
        return out.values()

    @api.model
    def getGuarantes(self):
        out = []
        for track in self.mold_id.mold_tracking:
            row = {'product': track.product_id.display_name,
                   'stampate_prodotte': emptyCaharIfFalse(track.lot_id.n_shots_guarantee),
                   'stampate_garanzia': emptyCaharIfFalse(track.lot_id.n_shots),
                   'stampate_msg': 'garanzia Scaduta' if track.lot_id.no_more_guarantee else ''}
            out.append(row)
        return out
