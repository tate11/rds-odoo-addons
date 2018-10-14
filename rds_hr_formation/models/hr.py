# -*- encoding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class RdsHrCourse(models.Model):
    _name = "rds.hr.course"
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _rec_name = 'complete_name'
    _order = 'parent_left'

    name = fields.Char("Nome Corso", required=True)
    complete_name = fields.Char(
        'Nome Completo', compute='_compute_complete_name',
        store=True)

    description = fields.Text("Descrizione")

    parent_id = fields.Many2one('rds.hr.course', string='Corsi Genitori', index=True, ondelete='cascade')
    child_id = fields.One2many('rds.hr.course', 'parent_id', string='Corsi Figli')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    
    material = fields.Many2many('rds.ir.document', string="Documenti Formativi")

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for course in self:
            if course.parent_id:
                course.complete_name = '%s / %s' % (course.parent_id.complete_name, course.name)
            else:
                course.complete_name = course.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True

class RdsHrFormation(models.Model):
    _name = "rds.hr.formation"

    course_id = fields.Many2one('rds.hr.course', required=True, string="Corso",  ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', required=True, string="Dipendente",  ondelete="cascade")
    ateneum = fields.Many2one("res.partner", string="Partner Erogatore")

    date = fields.Date("Data", required=True)
    
    certificate = fields.Many2one('rds.ir.document', string="Certificato")

class RdsHrSkillType(models.Model):
    _name = "rds.hr.skill.type"
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _rec_name = 'complete_name'
    _order = 'parent_left'

    name = fields.Char("Nome Corso", required=True)
    complete_name = fields.Char(
        'Nome Completo', compute='_compute_complete_name',
        store=True)

    description = fields.Text("Descrizione")

    parent_id = fields.Many2one('rds.hr.skill.type', string='Corsi Genitori', index=True, ondelete='cascade')
    child_id = fields.One2many('rds.hr.skill.type', 'parent_id', string='Corsi Figli')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for course in self:
            if course.parent_id:
                course.complete_name = '%s / %s' % (course.parent_id.complete_name, course.name)
            else:
                course.complete_name = course.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive categories.'))
        return True


class RdsHrSkill(models.Model):
    _name = "rds.hr.skill"

    skill_type = fields.Many2one('rds.hr.skill.type', required=True, string="Abilità",  ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', required=True, string="Dipendente",  ondelete="cascade")

    current_level = fields.Integer("Livello Attuale")
    current_target = fields.Integer("Target Attuale")
    
    ideal_level = fields.Integer("Livello Ideale")
    target_date = fields.Date("Target da raggiungere entro")
    notes = fields.Text("Note")

    @api.model
    def create(self, vals):
        self.env["rds.hr.skill.log"].create({
            'log_type': 'create',
            'skill_type': vals['skill_type'],
            'employee_id': vals['employee_id'],
            'level': vals['current_level'],
            'notes': vals['notes']
        })

        return super(RdsHrSkill, self).create(vals)

    @api.multi
    def write(self, vals):
        for i in self:
            logtype = 'note'
            if 'current_level' in vals:
                if vals['current_level'] > i.current_level:
                    logtype = 'increase'
                elif vals['current_level'] < i.current_level:
                    logtype = 'decrease'

            self.env["rds.hr.skill.log"].create({
                'log_type': logtype,
                'skill_type': i.skill_type.ids[0],
                'employee_id': i.employee_id.ids[0],
                'level': vals.get('current_level', i.current_level),
                'increment': vals.get('current_level', i.current_level) - i.current_level,
                'notes': vals.get('notes', i.notes)
            })

        super(RdsHrSkill, i).write(vals)

    @api.multi
    def unlink(self):
        for i in self:
            self.env["rds.hr.skill.log"].create({
                'log_type': 'delete',
                'skill_type': i.skill_type.ids[0],
                'employee_id': i.employee_id.ids[0],
            })
        super(RdsHrSkill, self).unlink()


class RdsHrSkillLog(models.Model):
    _name = "rds.hr.skill.log"

    skill_type = fields.Many2one('rds.hr.skill.type', required=True, string="Abilità",  ondelete="cascade")
    employee_id = fields.Many2one('hr.employee', required=True, string="Dipendente",  ondelete="cascade")

    log_type = fields.Selection(selection=[
                                ('create', 'Abilità Creata'),
                                ('increase', 'Incremento'),
                                ('decrease', 'Decremento'),
                                ('delete', 'Abilità Cancellata'),
                                ('note', 'Nota')                                
                                ], string="Tipo di log", required=True)

    level = fields.Integer("Livello")
    
    increment = fields.Integer("Incremento")
    notes = fields.Text("Note")
    
    date = fields.Date("Data", default=fields.Date.today(), required=True)


class Employee(models.Model):
        
    _name = 'hr.employee'
    _inherit = ['hr.employee']

    formations = fields.One2many("rds.hr.formation", "employee_id", string="Formazione")
    skills = fields.One2many("rds.hr.skill", "employee_id", string="Abilità")
    skill_logs = fields.One2many("rds.hr.skill.log", "employee_id", string="Abilità")