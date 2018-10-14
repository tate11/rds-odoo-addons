# -*- coding: utf-8 -*-

import collections
from functools import partial

import babel.dates
from dateutil.relativedelta import relativedelta, MO, SU

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import pycompat

_GRID_TUP = [('flaggrid', "Flags Grid")]


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=_GRID_TUP)

class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=_GRID_TUP)