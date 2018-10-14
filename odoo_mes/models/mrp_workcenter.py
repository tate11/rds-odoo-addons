# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import models, fields, api

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging, datetime

def f2dt(field):
    if field:
        return datetime.datetime.strptime(field, DEFAULT_SERVER_DATETIME_FORMAT)
    else:
        return datetime.datetime.now()

class MesInterval():
    def __init__(self, color, width, start):
        self.color = color
        self.width = width
        self.start = start

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    nominal_cycle_time = fields.Float("Current Cycle Time")
    auto_tracking = fields.Boolean("Manual Timetracking", oldname="allow_manual_tracking", default=False)

    def _compute_interval_size(self, from_dt=False):
        self.ensure_one()

        if not from_dt:
            from_dt = datetime.datetime.now().replace(hour=10,minute=0,second=0,microsecond=0)
        
        to_dt = datetime.datetime.now().replace(hour=22,minute=0,second=0,microsecond=0)

        _intervals = self.sudo().env['mrp.workcenter.productivity'].search(['&',
                                                                           ('workcenter_id', '=', self.ids[0]),
                                                                           '|',
                                                                           ('date_end', '>=', from_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
                                                                           ('date_end', '=', False)]).sorted(lambda x: str(x.date_end), reverse=True)
        out = list()
        if not _intervals:
            return out

        if f2dt(_intervals[0].date_end) <= to_dt:
            out.append(MesInterval('F2F2F2', (to_dt - f2dt(_intervals[0].date_end)).total_seconds()/(36*12),  f2dt(_intervals[0].date_end)))
           
        for i in _intervals:
            end = f2dt(i.date_end)

            if bool(out) and (out[-1].start > end):
                out.append(MesInterval('F2F2F2', (out[-1].start - f2dt(i.date_end)).total_seconds()/(36*12), f2dt(i.date_end)))
            
            out.append(MesInterval(i.loss_id.color, (min(f2dt(i.date_end), to_dt) - f2dt(i.date_start)).total_seconds()/(36*12), f2dt(i.date_start)))

        if bool(out) and (out[-1].start > from_dt):
            out.append(MesInterval('F2F2F2', (out[-1].start - from_dt).total_seconds()/(36*12),  from_dt))
        
        return out

    def format_oee(self):
        self.ensure_one()

        r = int(min(max(0, 255 * (1 - self.oee/100)), 255))
        g = int(min(max(0, 255 * self.oee/100), 255))
        b = 30

        return '#%02x%02x%02x' % (r, g, b)

    def get_active_workorder(self, dtf):
        self.ensure_one()
        workorder_id = self.env['mrp.workorder'].search([('workcenter_id', '=', self.id),
                                                         ('date_start', '<=', dtf),
                                                         ('state', '=', 'progress')], limit=1)
        if workorder_id:
            return workorder_id

        return False