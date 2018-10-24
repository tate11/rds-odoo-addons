# Intended for sole use by RDS Moulding Technology SpA. See README file.

from odoo import api, fields, models
import logging

class HrLul(models.Model):
    _name = 'hr.lul'

    year = fields.Integer("Year", readonly=True)
    month = fields.Selection([
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December')
        ], required=True, readonly=False)

    lul_days = fields.One2many('hr.lul.day', 'lul_id', string="Lul days")


class HrLulDay(models.Model):
    _name = 'hr.lul.day'

    def _get_dayoftheweek(self):
        pass

    date = fields.Date("Date", readonly=True)

    dayoftheweek = fields.Char("Day", compute=_get_dayoftheweek)