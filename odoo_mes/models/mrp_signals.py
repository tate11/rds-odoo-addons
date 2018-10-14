# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import models, fields, api, _

from ..mes_interfaces.lib import signals
import logging, datetime

_logger = logging.getLogger(__name__)

def toDT(date):
    return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    
def toFD(date):
    return date.strftime("%Y-%m-%d %H:%M:%S")

def FDnow():
    return toFD(datetime.datetime.now())

code_info = _("""
#---------------------------------------------------------------------------------------+
#   KONTRORU Scripts
#   This script will be evalued against each signal call. Local parameters passed:
#   
#   workcenter  -- This signal's workcenter object
#   env         -- Running environment
#   signal      -- The signal object
#   call        -- The signal.call object
#   log         -- Current system logger
#
#---------------------------------------------------------------------------------------+
""")


class MrpWorkcenterSignal(models.Model):
    _name = "mrp.workcenter.signal"

    name = fields.Char("Signal Name")
    
    signal_type = fields.Selection(selection=signals.SIGNALS_DESCRIPTIONS, string="Signal Type")
    workcenter_id = fields.Many2one("mrp.workcenter", "Workcenter")

    from_coil = fields.Integer("Starting Coil")
    signal_lenght = fields.Integer("Signal Length")

    frequency = fields.Integer("Update Frequency [ms]")

    code = fields.Text("Code", default=code_info)
    builtin_script = fields.Selection([
                                       ('kontroru___cycle_ft', "Forced-time Cycle"),
                                       ('kontroru___realtime_cycle_ft', "Real-Time Forced-Time Cycle")
                                      ],
                                       "Built-in Scripts")

    @api.model
    def get_signal_map(self):
        out = list()
        
        for i in self.search([]):
            out.append([i.from_coil, i.signal_type, i.name, i.id])

        return out


    @api.model
    def signal_call(self, kwargs):
        rec = self.browse(kwargs['signal_id'])
        try:
            if rec.builtin_script and getattr(rec, rec.builtin_script, False):
                getattr(rec, rec.builtin_script, False)()
            else:  
                c = compile(rec.code.strip(), "", "exec")
                eval(c, {'datetime': datetime, 'log': _logger}, {'workcenter': rec.workcenter_id, 'env': self.env, 'signal': rec})

            return True
            
        except Exception as e:
            logging.warning(e)
            return False



##### KONTRORU SCRIPTS
    @api.multi
    def kontroru___realtime_cycle_ft(self, *args, **kwargs):

        STILL      = self.env['ir.config_parameter'].sudo().get_param('odoo_mes.mes_loss_still_id')
        SETUP = self.env['ir.config_parameter'].sudo().get_param('odoo_mes.mes_loss_setup_id')
        PRODUCTIVE = self.env['ir.config_parameter'].sudo().get_param('odoo_mes.mes_loss_productive_id')
        PRODUCTIVE_ANOMALY = self.env['ir.config_parameter'].sudo().get_param('odoo_mes.mes_loss_productive_anomaly_id')

        WCPRD = self.env['mrp.workcenter.productivity']
        WKORD = self.env['mrp.workorder']

        workcenter = self.workcenter_id
        workorder = workcenter.get_active_workorder(fields.Datetime.now())

        lc = WCPRD.search([('workcenter_id','=',workcenter.id)], limit=1)
        signal_time = fields.datetime.now()
        signal_time_st = fields.Datetime.now()
        tolerance = (1 + 0.3)

        if lc:
            

            if lc.date_end:
                if lc.date_end != signal_time_st:
                    WCPRD.create({'workcenter_id': workcenter.id, 'workorder_id': workorder and workorder.id, 'loss_id': (lc.workorder_id == workorder) and STILL or SETUP, 
                                'date_end': signal_time_st, 'date_start': lc.date_end})
                WCPRD.create({'workcenter_id': workcenter.id, 'workorder_id': workorder and workorder.id, 'loss_id': workorder and PRODUCTIVE or PRODUCTIVE_ANOMALY, 
                            'date_start': signal_time_st, 'nominal_cycle': workorder and (workorder.operation_id.time_cycle or workorder.qty_production/workorder.duration_expected) or 0
                            })
            else:
                if lc.loss_id.loss_type in ['productive', 'performance']:
                    if (not workorder) and (not lc.workorder_id):
                        lc.write({'cycles': lc.cycles+1, 'date_last_cycle': signal_time_st})
                        return  

                    if workorder != lc.workorder_id:
                        lc.write({'date_end': signal_time_st})
                        WCPRD.create({'workcenter_id': workcenter.id, 'workorder_id': workorder and workorder.id, 'loss_id': workorder and PRODUCTIVE or PRODUCTIVE_ANOMALY, 
                            'date_start': signal_time_st, 'nominal_cycle': workorder and (workorder.operation_id.time_cycle or workorder.qty_production/workorder.duration_expected) or 0
                            })
                        return  

                    if (signal_time - toDT(lc.date_last_cycle or lc.date_start)).total_seconds()/60 <= lc.nominal_cycle * tolerance:
                        lc.write({'cycles': lc.cycles+1, 'date_last_cycle': signal_time_st})
                        workorder.advance()
                    else:
                        if not lc.date_last_cycle:
                            lc.date_last_cycle = toFD(toDT(lc.date_last_cycle) + datetime.timedelta(0.0007))

                        lc.write({'date_end': lc.date_last_cycle})
                        WCPRD.create({'workcenter_id': workcenter.id, 'workorder_id': workorder and workorder.id, 'loss_id': STILL, 
                                    'date_end': signal_time_st, 'date_start': lc.date_last_cycle})
                        WCPRD.create({'workcenter_id': workcenter.id, 'workorder_id': workorder and workorder.id, 'loss_id': workorder and PRODUCTIVE or PRODUCTIVE_ANOMALY, 
                            'date_start': signal_time_st, 'nominal_cycle': workorder and (workorder.operation_id.time_cycle or workorder.qty_production/workorder.duration_expected) or 0
                            })                            
                
                else:
                    lc.write({'date_end': signal_time_st})
                    WCPRD.create({'workcenter_id': workcenter.id, 'workorder_id': workorder and workorder.id, 'loss_id': workorder and PRODUCTIVE or PRODUCTIVE_ANOMALY, 
                        'date_start': signal_time_st, 'nominal_cycle': workorder and (workorder.operation_id.time_cycle or workorder.qty_production/workorder.duration_expected) or 0
                        })                    

        else:
            WCPRD.create({'workcenter_id': workcenter.id, 'workorder_id': workorder and workorder.id, 'loss_id': workorder and PRODUCTIVE or PRODUCTIVE_ANOMALY, 
                       'date_start': signal_time_st, 'nominal_cycle': workorder and (workorder.operation_id.time_cycle or workorder.qty_production/workorder.duration_expected) or 0
                      })