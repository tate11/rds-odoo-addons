# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution    
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    $Id$
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
Created on Mar 30, 2016

@author: Daniel Smerghetto
'''
import os
import tempfile
import datetime
import base64
import logging
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import osv
from odoo import tools
from odoo.exceptions import UserError


class RdsExtentionDownload(models.TransientModel):
    _name = 'rds_extention_download'
    
    file_name = fields.Char(string="Filename", default="F_Attivita.CSV")
    fileStorage = fields.Binary(_("File"))


class RdsExtentionUpload(models.TransientModel):
    _name = 'rds_extention_upload'
    fileStorage = fields.Binary(_("File"))

    @api.multi
    def inport_project(self):
        mrp_workorder_obj = self.env['mrp.workorder']
        for obj in self:
            mrp_workorder_obj.import_from_project(obj)


class ExportProductionCSV(models.TransientModel):
    _name = "export.production_csv"

    @api.multi
    def generate_report(self):
        orderObj = self.env['sale.order']
        obj = orderObj.generateData()
        strVal = obj.createCsv()
        tmpFile = os.path.join(tempfile.gettempdir(), self.datas_name)
        with open(tmpFile, 'w') as fileObj:
            fileObj.write(strVal)
        with open(tmpFile, 'rb') as fileObj:
            self.datas = base64.encodestring(fileObj.read())

        return {'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': ExportProductionCSV._name,
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
                }

    @api.model
    def _compute_default_file_name(self):
        return 'Production_%s.csv' % (datetime.date.today())

    datas = fields.Binary("Download",
                          readonly=True,
                          )

    datas_name = fields.Char('Download file name',
                             size=255,
                             required=True,
                             default=_compute_default_file_name)
