from odoo import fields, models


class InvoiceMenu(models.Model):
    _name = "timesheet.product.change"
    _description = "Timesheet Product Change"

    product_id = fields.Many2one('product.product', string='Product', required=True)

    def change_timesheet_product(self):
        if 'account_analytic_ids' in self.env.context:
            for analytic_line in self.env.context['account_analytic_ids']:
                analytic_line_id = self.env['account.analytic.line'].browse(analytic_line)
                analytic_line_id.write({'product_type': self.product_id.id})
