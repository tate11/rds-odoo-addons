'''
Created on 12 Jul 2018

@author: mboscolo
'''

import io
import csv
import base64
import werkzeug
import requests
from odoo import _
from odoo import api
from odoo import models
from odoo import fields
from datetime import datetime
from odoo.tools import float_compare
from odoo.tools import float_round
from odoo.tools import float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.http import request


ODOO_PROJECT = {'A0142': 'A0142-1 - 320 T COLOSIO',
                'A0035': 'A0035-2 - 250 T COLOSIO',
                'A0103': 'A0103-3 - 320 T STP',
                'A0138': 'A0138-4 - 490 T STP',
                'A0217': 'A0217-5 - 590 T STP',
                'A0218': 'A0218-6 - 560 T COLOSIO',
                'A0154': 'A0154-7 - 800 T STP OLK',
                'A0034': 'A0034-8 - 600 T COLOSIO',
                'A0219': 'A0219-9 - 320 T IDRA',
                'APS': 'Area Preparazione Stampi',
                'A0220': 'A0220-A - 750 T COLOSIO'}

PROJECT_ODOO = dict([(v, k) for k, v in ODOO_PROJECT.items()])


class MrpProduction(models.Model):
    _inherit = 'mrp.workorder'

    @api.model
    def search_update_task(self, id, start, stop, wcBrws=None):
        mrp_workorder = self.search([('id', '=', id)])
        if mrp_workorder and mrp_workorder.state not in ['cancel', 'done']:
            mrp_workorder.date_planned_start = start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            mrp_workorder.date_planned_finished = stop.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            if mrp_workorder.workcenter_id.id != wcBrws.id:
                mrp_workorder.workcenter_id = wcBrws.id

    @api.model
    def checkCreateWorkCenter(self, code):
        wcObj = self.env['mrp.workcenter']
        for wcBrws in wcObj.search([('code', '=', code)]):
            return wcBrws
        raise UserError(_('Il workcenter %r non è presente in Odoo' % (code)))
    
    @api.model
    def import_from_project(self, objFrom):
        output = io.StringIO()
        output.write(base64.b64decode(objFrom.fileStorage).decode(encoding='iso-8859-1', errors='strict'))
        output.seek(0)
        reader = csv.reader(output, delimiter=';')
        for row in reader:
            id = row[1].split('_')[-1]
            start = datetime.strptime(row[2][4:], "%d/%m/%y")  # Mon 13/08/18
            stop = datetime.strptime(row[3][4:], "%d/%m/%y")
            
            code = PROJECT_ODOO.get(row[4])
            wcBrws = self.checkCreateWorkCenter(code)
            self.search_update_task(id, start, stop, wcBrws)
        output.close()

    @api.multi
    def export_to_project(self):
        """
        Nome    Q0001256_E284180_900089700_BLOCCHETTO_VW_GUIDA_
        ID    1
        Durata    0 m
        Modalita attivita    Programmazione automatica
        Tipo di vincolo      Iniziare non prima del
        Inizio    05/05/2018 11:12
        Scadenza    29/03/2018
        Nomi risorse    A0217-5 - 590 T STP
        Testo1    Q0001256
        Testo2    9050005
        Testo3    11
        Testo4    S
        Testo5    2018Q0001256
        Testo7
        Testo8    -71715
        Testo9    5 - 590 T STP
        Testo20    Q0001256
        Testo21    2018
        Testo22    E284180
        Testo23    40
        Testo24    A0217
        Testo25    ALAUT
        Testo26    -8605.8 m
        Testo27    240 m
        Testo17    S
        Testo18    160233
        Testo19    PROD
        """
        index = 0
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_NONE, delimiter=';', quotechar='')
        header = ["Nome",
                  "ID",
                  "Durata",
                  "Modalità attività",
                  "Tipo di vincolo",
                  "Inizio",
                  "Scadenza",
                  "Nomi risorse",
                  "Testo1",
                  "Testo2",
                  "Testo3",
                  "Testo4",
                  "Testo5",
                  "Testo7",
                  "Testo8",
                  "Testo9",
                  "Testo20",
                  "Testo21",
                  "Testo22",
                  "Testo23",
                  "Testo24",
                  "Testo25",
                  "Testo26",
                  "Testo27",
                  "Testo17",
                  "Testo18",
                  "Testo19"]
        writer.writerow(header)
        for mrp_workorder_id in self.search([('id', 'in', self.env.context.get('active_ids'))]):
            production_id = mrp_workorder_id.production_id
            index = index + 1
            anno = production_id.create_date.split('-')[0]
            # 'nome':
            date_planned_start = datetime.strptime(mrp_workorder_id.date_planned_start, DEFAULT_SERVER_DATETIME_FORMAT)  # 'inizio':
            date_planned_finished = datetime.strptime(mrp_workorder_id.date_planned_finished, DEFAULT_SERVER_DATETIME_FORMAT)  # 'scadenza':
            work_center_name = mrp_workorder_id.workcenter_id.code
            work_center_name = ODOO_PROJECT.get(work_center_name, work_center_name)
            row = [str(production_id.name) + "_" + str(production_id.product_id.default_code) + "_" + str(production_id.mold_id.serial_no) + "_" + str(production_id.product_id.name) + "_" + str(mrp_workorder_id.id),
                   index,  # 'id':
                   str(int(mrp_workorder_id.duration_expected)) + " m",  # 'durata':
                   'Programmazione automatica',  # 'modalita operatiova':
                   'Iniziare non prima del',  # 'tipo di vincolo':
                   date_planned_start.strftime("%d/%m/%Y %H:%M"),  # 'inizio':
                   date_planned_finished.strftime("%d/%m/%Y"),  # 'scadenza':
                   work_center_name,  # 'nome_risorse':
                   production_id.name,  # 'testo1':
                   production_id.mold_id.serial_no,  # 'testo2':
                   '11',  # 'Testo3':
                   'S' if production_id.mold_id.have_active_maintenance() else 'N',  # 'Testo4': # manuntenzioni [  S/N -> in manutenzione]
                   anno + production_id.name,  # 'Testo5':
                   '',  # 'Testo7':
                   int(mrp_workorder_id.qty_remaining),  # 'Testo8': quantita' residua
                   work_center_name,  # 'Testo9':
                   production_id.name,  # 'Testo20':
                   anno,  # 'Testo21':
                   production_id.product_id.default_code,  # 'Testo22':
                   '40',  # 'Testo23':
                   work_center_name,  # 'Testo24':
                   mrp_workorder_id.name,  # 'Testo25':
                   '-8605.8 m',  # 'Testo26':
                   str(int(mrp_workorder_id.duration_expected)) + ' m',  # 'Testo27':
                   'S',  # 'Testo17':
                   int(mrp_workorder_id.qty_production),  # 'Testo18':
                   'PROD',
                   '']  # 'Testo19':
            writer.writerow(row)
        objNew = self.env['rds_extention_download'].create({'fileStorage': base64.b64encode(output.getvalue().encode('iso-8859-1'))}) # Eventually latin-1 
        action = {'name': 'OpenWizard',
                  'view_type': 'form',
                  'view_mode': 'form',
                  'target': 'new',
                  'res_id': objNew.id,
                  'res_model': 'rds_extention_download',
                  'type': 'ir.actions.act_window'}
        return action
