'''
Created on 27 Jul 2018

@author: mboscolo
'''

import io
from datetime import datetime
from dateutil import tz
import base64
from odoo import _
from odoo import api
from odoo import models
from odoo.exceptions import UserError
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger


class ReportProductionPdf(models.AbstractModel):
    _name = 'report.rds_extension.report_standard_lables'

    @api.model
    def get_report_values(self, docids=None, data=None):
        return {'docs': data}
