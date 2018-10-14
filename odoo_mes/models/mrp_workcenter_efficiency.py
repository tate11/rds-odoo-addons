# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import models, fields, api
import datetime

def toDT(date):
    return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    

class MrpWorkcenteEfficiency(models.Model):
    _inherit = "mrp.workcenter.productivity"

    def is_late(self):
        delta = (toDT(self.date_last_cycle or self.date_start) - fields.datetime.now()).total_seconds()/60
        if delta >= (self.nominal_cycle and self.nominal_cycle*1.5) or 2:
            return True
        return False

    @api.model
    def cron_autoclose_late(self):
        ids = self.env['mrp.workcenter'].search([('auto_tracking', '=', False)]).ids

        STILL = self.env['ir.config_parameter'].sudo().get_param('odoo_mes.mes_loss_still_id')

        if ids:
            lc = self.env['mrp.workcenter.productivity'].search([('workcenter_id', 'in', ids),('loss_type', 'in', ['performance', 'productive']),('date_end','=',False)])
            for i in lc: 
                if i.is_late():
                    workorder = i.workcenter_id.get_active_workorder(fields.Datetime.now())
                    lc.write({'date_end': fields.Datetime.now()})
                    self.create({'workcenter_id': i.workcenter_id.id, 'workorder_id': workorder and workorder.id, 'loss_id': STILL, 'date_start': fields.Datetime.now()})      



    @api.depends('date_end', 'date_start', 'date_last_cycle')
    def _compute_duration(self):
        for blocktime in self:
            if blocktime.date_end:
                d1 = fields.Datetime.from_string(blocktime.date_start)
                d2 = fields.Datetime.from_string(blocktime.date_end)
                diff = d2 - d1
                blocktime.duration = round(diff.total_seconds() / 60.0, 2)
            elif blocktime.date_last_cycle:
                d1 = fields.Datetime.from_string(blocktime.date_start)
                d2 = fields.Datetime.from_string(blocktime.date_last_cycle)
                diff = d2 - d1
                blocktime.duration = round(diff.total_seconds() / 60.0, 2)
            else:
                blocktime.duration = 0.0

    def _compute_avg_cycletime(self):
        for i in self:
            if i.cycles <= 0:
                continue

            i.average_cycle = i.duration / i.cycles

    def _compute_efficiency(self):
        for i in self:
            if i.average_cycle <= 0:
                continue
            
            i.efficiency = (i.nominal_cycle / i.average_cycle)

    date_last_cycle = fields.Datetime('Last Cycle End', oldname='last_cycle_end')

    cycles = fields.Integer('Number of Cycles')

    average_cycle = fields.Float("Average Cycle Time", compute=_compute_avg_cycletime)
    nominal_cycle = fields.Float("Nominal Cycle Time")

    efficiency = fields.Float("Efficiency", compute=_compute_efficiency)


class MrpWorkcenteEfficiencyLoss(models.Model):
    _inherit = "mrp.workcenter.productivity.loss"

    color = fields.Char("HTML Color")