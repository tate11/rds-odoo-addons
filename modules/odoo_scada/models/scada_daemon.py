# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.service.server import Worker

import subprocess

import logging, traceback, time

# LIBRARIES
import pymodbus.client.sync as pymcs

lenghts = {
    'bool': 1,
    'int64': 64
}

def bitarr2binarystr(value):
    return '0b' + ''.join(['1' if x else '0' for x in value])[::-1]

def binarystr2int(value):
    return int(value, 2)

# Classes

class ScadaDevice(models.Model):
    _name = "scada.device"
    _description = "SCADA Device"

    name = fields.Char("Device Name")

    ip_address = fields.Char("IP Address")
    port = fields.Integer("Device Port")

    device_type = fields.Selection(selection=[('server_modbus', 'Modbus/TCP Server')], string="Device Type")

    values = fields.One2many('scada.value', 'device', "Values")
    events = fields.One2many('scada.event', 'device', "Events")

    def scada_read(self):
        self.values.scada_read()

class ScadaValue(models.Model):
    _name = "scada.value"
    _description = "SCADA Value"

    name = fields.Char("Value Name")
    device = fields.Many2one('scada.device', string='Device')
    events = fields.One2many('scada.event', 'value', "Events")

    device_type = fields.Selection(selection=[('server_modbus', 'Modbus/TCP Server')], related="device.device_type", string="Device Type", readonly=True)

    index = fields.Integer("Starting Index")
    read_method = fields.Many2one('scada.value.readmethod', string='Read Method')
    value_type = fields.Selection([('bool', 'Boolean'),('int64', '64-bit Integer')], string="Value Type")

    value = fields.Char("Last Value", readonly=True)
    polling_time = fields.Integer("Polling Interval", digits=(8,4))

    nextcall = fields.Float("Next Reading", default=lambda x: time.time(), digits=(30,4))

    error_log = fields.Text("Error Log")

    @api.model
    def read_hook(self):
        now = time.time()
        self.search([('nextcall', '<=', now)]).scada_read(now)

    def scada_read(self, now=time.time()):
        for i in self:
            try:
                if i.read_method.code == "tcp_read_coils":
                    client = pymcs.ModbusTcpClient(i.device.ip_address, i.device.port)
                    value = client.read_coils(i.index, lenghts[i.value_type]).bits
                    logging.warning(value)
                else:
                    value = [False]*lenghts[i.value_type]
                    i.nextcall = now + i.polling_time

                i.value = i.encode(value)
            except:
                i.error_log = "{}\n{}".format(i.errorlog, traceback.format_exc())
                continue
        
        self.checkdo_events()

    def checkdo_events(self):
        for i in self:
            for e in i.events:
                if e.single_shot and e.fired:
                    toRefresh = eval(e.unfire_conditions, {}, {'value': e.value.value})
                    if toRefresh:
                        e.fired = False
                else:
                    toTrigger = eval(e.conditions, {}, {'value': e.value.value})
                    if toTrigger:
                        e.run()

    def encode(self, value):
        if self.value_type == 'bool':
            return value[0]
        if self.value_type == 'int64':
            return binarystr2int(bitarr2binarystr(value))

class ScadaReadMethod(models.Model):
    _name = "scada.value.readmethod"
    _description = "SCADA Read Method"

    name = fields.Char("Method Name")
    code = fields.Char("Code")

    device_type = fields.Selection(selection=[('server_modbus', 'Modbus/TCP Server')], string="Device Type")


class ScadaEvent(models.Model):
    _name = "scada.event"
    _inherit = 'ir.actions.server'
    _description = "SCADA Event"

    name = fields.Char("Event Name")
    device = fields.Many2one('scada.device', 'Device')
    value = fields.Many2one('scada.value', 'SCADA Value')

    conditions = fields.Char("Conditions", help="Must be a single python statement, with \"value\" being triggerig value. e.g: value >= 20000")
    unfire_conditions = fields.Char("Refresh Conditions", help="Once the event has been fired, these conditions needs to be met before it can be fired again.")

    single_shot = fields.Boolean("Single Shot")
    fired = fields.Boolean("Event Fired")

    action_id = fields.Many2one("ir.actions.server", "Server Action", help="This action will be triggered when the event fires.")
    context = fields.Char("Action Context", help="This context will be passed to triggered server actions. You can also use it to pass parameters. It must has the shape of a python dictionary.", default="{'active_id': 1, 'active_ids': [1], 'active_model': 'mrp.workcenter', 'active_domain': []}")

    @api.model
    def _get_eval_context(self, action=None):
        eval_context = super(ScadaEvent, self)._get_eval_context(action)
        if self._context.get('scada_value'):
            eval_context.update({
                'scada_value': self._context.get('scada_value')
            })

        return eval_context

