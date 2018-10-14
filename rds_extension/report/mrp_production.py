'''
Created on 12 Jul 2018

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
    _name = 'report.rds_extension.mrp_production_multi_pdf'

    @api.model
    def render_qweb_pdf(self, mrp_production_ids=None):
        documents = []
        pdfWriter = PdfFileWriter()
        for mrp_production_id in mrp_production_ids:
            documents += mrp_production_id.getAllReportPdf()
            for document in documents:
                if isinstance(document, tuple):
                    document = document[0]
                newReader = PdfFileReader(io.BytesIO(document), overwriteWarnings=False)
                for page in newReader.pages:
                    pdfWriter.addPage(page)

        byteString = ''
        with io.BytesIO() as f:
            pdfWriter.write(f)
            value_to_write = f.getvalue()
            byteString =  base64.b64encode(value_to_write) # b"data:application/pdf;base64," +
        return byteString.decode('UTF-8')
    

    @api.model
    def get_report_values(self, docids, data=None):
        mrp_production_ids = self.env['mrp.production'].browse(docids)
        return {'docs': mrp_production_ids,
                'get_content': self.render_qweb_pdf}
