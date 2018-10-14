'''
Created on 4 Jul 2018

@author: mboscolo
'''
import logging
import requests
import time
import pytz
from urllib.parse import urlparse
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
from odoo import registry
from docutils.nodes import description
from odoo import tools
DATETIME_CONVERTION = '%d/%m/%y %H:%M:%S'
DELTA_TIME = 0
PRODUCTIVITY_REASON_MAP = {'CONTA_STAMPATE_PRODOTTE': 21,    # Tempo Produttivo
                           'ERROR': 16,                      # Rottura di Attrezzature
                           'CONTA_PZ_SCARTI': 19}            # difetti


def parseDate(date, time):
    """
    parse date time getting back the datetime object
    """
    date_time = time.strip() + " " + date.strip()
    return datetime.strptime(date_time, DATETIME_CONVERTION)


def parseLine(line):
    line = line.strip()
    if len(line) > 0:
        args = line.split(';')
        if args:
            return {'machine': args[0][0:5].strip(),
                    "comando": args[0][6:29].strip(),
                    "datetime": parseDate(args[1][:8], args[1][8:]),
                    "flag": args[3].strip(),
                    'content': line
                    }
    return {}


def deParseLine(line):
    return "".join(line.values())


class MachineLines(object):
    def __init__(self, machineName, lines=[]):
        self._machineName = machineName
        self._lines = {}
        if lines:
            self.addLines(lines)

    def addLines(self, lines):
        for line in lines:
            machine = line.get('machine')
            if machine == self._machineName:
                self._lines[line.get('datetime')] = line
            else:
                logging.warning("Row with machine name not match %r - %r" % (machine, self._machineName))

    def getOldLine(self):
        out = ""
        for line in self._lines.values():
            out = out + line.get('content') + '\r\n'
        return out

    def getRemoveGoodLine(self):
        goodLines = []
        errors = []
        sorted_keys = list(self._lines.keys())
        sorted_keys.sort()
        transaction_open = False
        pack_vals = []
        toRemove = []
        for key in sorted_keys:
            row = self._lines[key]
            if transaction_open:
                pack_vals.append(row)
                if row.get('comando') == "CONTA_STAMPATE_PRODOTTE" and row.get('flag') == 'D':
                    toRemove.append(key)
                    if len(pack_vals) == 2:
                        start_time = pack_vals[0].get("datetime")
                        end_time = pack_vals[1].get("datetime")
#                         if pack_vals[1].get('flag').upper() == 'U':
#                             start_time = pack_vals[1].get("datetime")
#                             end_time = pack_vals[0].get("datetime")
                        description = ''
                        for row in pack_vals:
                            description += row.get('content')
                        goodLines.append({'workcenter_name': pack_vals[0].get('machine'),
                                          'date_start': start_time.replace(hour=start_time.hour - DELTA_TIME),
                                          'date_end': end_time.replace(hour=end_time.hour - DELTA_TIME),
                                          'loss_reason': pack_vals[0].get('flag'),
                                          'description': description})
                    elif len(pack_vals) != 2 and len(pack_vals) > 0:
                        dates = []
                        spool_msg = ""
                        out = {'workcenter_name': pack_vals[0].get('name')}
                        description = ''
                        for row in pack_vals:
                            dates.append(row.get("datetime"))
                            spool_msg = spool_msg + row.get('comando')
                            description += row.get('content')
                        out['loss_reason'] = spool_msg.replace("CONTA_STAMPATE_PRODOTTE", " ")
                        out['date_start'] = min(dates)
                        out['date_end'] = max(dates)
                        out['description'] = description
                        errors.append(out)
                    transaction_open = False
                    for row in pack_vals:
                        toRemove.append(row.get('datetime'))
                    pack_vals = []
            else:
                if row.get('comando') == "CONTA_STAMPATE_PRODOTTE" and row.get('flag') == 'U':
                    transaction_open = True
                    pack_vals = [row]
        for k in toRemove:
            if k in self._lines:
                del self._lines[k]
        return goodLines, errors, self.getOldLine()


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    machine_path = fields.Char("Machine webServerPath")
    machine_user = fields.Char("Machine webServerPath")
    machine_password = fields.Char("Machine Password")
    machine_log = fields.Text("Machine Log", default="")

    @api.model
    def check_machine_electronic_boards(self, mail_from, mail_to):
        err_msg = ''
        for workcenter_id in self.search([]):
            if not workcenter_id.machine_path:
                continue
            parsed_uri = urlparse(workcenter_id.machine_path)
            request_uri = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            try:
                resp = requests.head(request_uri, timeout=2)
                #if resp.status_code != 200:
                #    err_msg += "Unable to retrieve information from %r with status %r \n" % (workcenter_id.machine_path, resp)
            except Exception as ex:
                    err_msg += "[%r] Unable to retrieve information from %r with status %r \n" % (workcenter_id.name, workcenter_id.machine_path, ex)
        if err_msg:
            email = self.env['ir.mail_server'].build_email(
                email_from=[mail_from],
                email_to=[mail_to],
                subject='Machine Workcenter error !!', body=err_msg,
            )
            self.env['ir.mail_server'].send_email(email)
        return True

    @api.multi
    def updateMachineLog(self):
        for workcenter_id in self:
            try:
                resp = requests.get(workcenter_id.machine_path, auth=(workcenter_id.machine_user, workcenter_id.machine_password))
                if resp.status_code != 200:
                    err_msg = "Unable to retrieve information from %r with status %r" % (workcenter_id.machine_path, resp)
                    logging.warning(err_msg)
                    return ""
                if not workcenter_id.machine_log:
                    workcenter_id.machine_log = ""
                new_list = set(resp.text.split('\r\n') + workcenter_id.machine_log.split('\r\n'))
                new_string = '\r\n'.join(new_list)
                workcenter_id.machine_log = new_string
            except Exception as ex:
                logging.error("Unable to process machine %r for %r" % (workcenter_id, ex))

    @api.model
    def updateAllMachineLog(self):
        self.search(['machine_path', '!=', False]).updateMachineLog()

    @api.one
    def getDeleteMachineLogParsered(self):
        if not self.machine_log:
            return {}
        split_with = '\r\n'
        if self.machine_log.find('\r\n') < 0:
            split_with = '\n'
        command_list = self.machine_log.split(split_with)
        command_dict = map(parseLine, command_list)
        ml = MachineLines(self.code, command_dict)
        goodLine, errorLines, noComutedLine = ml.getRemoveGoodLine()
        self.machine_log = noComutedLine
        self.createWorkCenterProd(goodLine)
        self.createWorkCenterError(errorLines)
        return command_dict

    @api.one
    def createWorkCenterProd(self, lines):
        loss_id = PRODUCTIVITY_REASON_MAP.get('CONTA_STAMPATE_PRODOTTE')
        self.create_mrp_workcenter_productivity(lines,
                                                self.id,
                                                loss_id,
                                                record_workorderQTY=True)

    @api.one
    def createWorkCenterError(self, lines):
        loss_id = PRODUCTIVITY_REASON_MAP.get('ERROR')
        self.create_mrp_workcenter_productivity(lines,
                                                self.id,
                                                loss_id)

    @api.model
    def create_mrp_workcenter_productivity(self, lines, workcenter_id, loss_id, record_workorderQTY=False):
        if not lines:
            return
        mrp_workcenter_productivity = self.env['mrp.workcenter.productivity']
        mrp_workcenter_productivity_id = mrp_workcenter_productivity.search([('workcenter_id', '=', workcenter_id)], order="id desc", limit=1)
        if mrp_workcenter_productivity_id.date_end:
            last_insert_date = fields.Datetime.from_string(mrp_workcenter_productivity_id.date_end)
        else:
            last_insert_date = fields.Datetime.from_string(mrp_workcenter_productivity_id.date_start)
        workorder_id = self.env['mrp.workorder'].search([('workcenter_id', '=', workcenter_id),
                                                         ('state', '=', 'progress'),
                                                         ('name', '=', 'ALAUT')], limit=1)

        def toUtc(fromDate, originalZone="Europe/Rome"):
            if not fromDate:
                return fromDate
            local = pytz.timezone(originalZone)
            local_dt = local.localize(fromDate, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            return utc_dt
        last_insert_date = toUtc(last_insert_date, "UTC")
        for line in lines:
            start_date = toUtc(line.get('date_start'))
            end_date = toUtc(line.get('date_end'))
            if not last_insert_date or last_insert_date < start_date:
                if workorder_id:
                    workorder_id.register_shot()
                line['loss_id'] = loss_id
                if 'CONTA_PZ_SCARTI' in line.get('description'):
                    line['loss_id'] = PRODUCTIVITY_REASON_MAP['CONTA_PZ_SCARTI']
                line['workcenter_id'] = workcenter_id
                if workorder_id:
                    line['workorder_id'] = workorder_id.id
                if mrp_workcenter_productivity_id and not mrp_workcenter_productivity_id.date_end:
                    mrp_workcenter_productivity_id.date_start = start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    mrp_workcenter_productivity_id.date_end = end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                else:
                    line['date_start'] = start_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    line['date_end'] = end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    # clean up element not needed for the creation
                    del line['loss_reason']
                    del line['workcenter_name']
                    mrp_workcenter_productivity.create(line)
                if workorder_id and record_workorderQTY:
                    workorder_id.qty_producing = workorder_id.production_id.getNImpronte(workorder_id.product_id)
                    workorder_id.record_production()

    @api.one
    def getUpdateLog(self):
        logging.info("UPDATE MACHINE %r" % self.name)
        self.updateMachineLog()
        self.getDeleteMachineLogParsered()

    @api.multi
    def cronMachine(self):
        cr = registry(self._cr.dbname).cursor()
        self = self.with_env(self.env(cr=cr))
        for _i in range(3):
            for workcenter_id in self.search([('machine_path', '!=', False)]):
                try:
                    workcenter_id.getUpdateLog()
                    cr.commit()
                except Exception as ex:
                    logging.error(ex)
                    cr.rollback()
                    logging.error("RollBack")
            time.sleep(20)
        cr.close()

    @api.model
    def cronMachineClient(self):
        for workcenter_id in self.search([('machine_path', '!=', False)]):
            try:
                workcenter_id.getUpdateLog()
            except Exception as ex:
                logging.error(ex)
                logging.error("RollBack")
        return True
