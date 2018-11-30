from odoo import api, fields, models, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    sale_ok = fields.Boolean('Can be Sold', default=True)
    purchase_ok = fields.Boolean('Can be Purchased', default=True)
    
    property_account_income_id = fields.Many2one('account.account', company_dependent=True,
        string="Income Account",
        domain=[('deprecated', '=', False)],
        help="Keep this field empty to use the default value from the product category.")
    property_account_expense_id = fields.Many2one('account.account', company_dependent=True,
        string="Expense Account",
        domain=[('deprecated', '=', False)],
        help="Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used.")
