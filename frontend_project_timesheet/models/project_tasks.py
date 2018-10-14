from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import math

def time_float(value):
    y, x = math.modf(value)
    return "{}:{}".format(int(x), int(y*60))

class ProjectTask(models.Model):
    _inherit = 'project.task'

    employee_id = fields.Many2one('hr.employee', 'Assigned Employee')
    work_start = fields.Datetime('On work since')

    def start_work(self):
        result = {'type': 'success'}
        if not self.work_start:
            self.work_start = fields.Datetime.now()
            result['message'] = _("Inizio il lavoro sul compito \"{}\"").format(self.name)
        else:
            td = fields.datetime.now() - fields.datetime.strptime(self.work_start, DEFAULT_SERVER_DATETIME_FORMAT)

            if (td.days == 0) and (td.seconds < 60):
                result['type'] = 'warning'
                result['message'] = _("Il tempo di lavoro è trobbo breve per essere registrato.")
                self.work_start = False
            else:
                self.work_start = False
                self.env['account.analytic.line'].create({
                                                'date': fields.date.today(),
                                                'employee_id': self.employee_id.id,
                                                'task_id': self.id,
                                                'project_id': self.project_id.id,
                                                'unit_amount': (td.days*24 + td.seconds/3600)
                                                })
                result['message'] = _("Scaricate {} ore sul compito \"{}\"").format(time_float((td.days*24 + td.seconds/3600)), self.name)
            
        
        result['datetime'] = self.work_start

        return result

    
    def block(self):
        result = {'type': 'success'}
        if not self.work_start:
            result['message'] = _("Il compito \"{}\" è stato bloccato.").format(self.name)
            self.kanban_state = 'blocked'
        else:
            td = fields.datetime.now() - fields.datetime.strptime(self.work_start, DEFAULT_SERVER_DATETIME_FORMAT)
            self.kanban_state = 'blocked'
            if (td.days == 0) and (td.seconds < 60):
                result['message'] = _("Il compito \"{}\" è stato bloccato senza scarico di ore.").format(self.name)
                self.work_start = False
            else:
                self.work_start = False
                self.env['account.analytic.line'].create({
                                                'date': fields.date.today(),
                                                'employee_id': self.employee_id.id,
                                                'task_id': self.id,
                                                'project_id': self.project_id.id,
                                                'unit_amount': (td.days*24 + td.seconds/3600)
                                                })
                result['message'] = _("Il compito \"{2}\" è stato bloccato dopo {1} ore di lavoro.").format(time_float((td.days*24 + td.seconds/3600)), self.name)
            
        

        return result


    def done(self):
        result = {'type': 'success'}
        if not self.work_start:
            result['message'] = _("Il compito \"{}\" è stato completato.").format(self.name)
            self.kanban_state = 'done'
        else:
            td = fields.datetime.now() - fields.datetime.strptime(self.work_start, DEFAULT_SERVER_DATETIME_FORMAT)
            self.kanban_state = 'done'
            if (td.days == 0) and (td.seconds < 60):
                result['message'] = _("Il compito \"{}\" è stato completato senza scarico di ore.").format(self.name)
                self.work_start = False
            else:
                self.work_start = False
                self.env['account.analytic.line'].create({
                                                'date': fields.date.today(),
                                                'employee_id': self.employee_id.id,
                                                'task_id': self.id,
                                                'project_id': self.project_id.id,
                                                'unit_amount': (td.days*24 + td.seconds/3600)
                                                })
                result['message'] = _("Il compito \"{2}\" è stato completato dopo {1} ore di lavoro.").format(time_float((td.days*24 + td.seconds/3600)), self.name)
            
        

        return result