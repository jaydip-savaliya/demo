from odoo import api, fields, models


class InvoicePricingDetails(models.Model):
    _name = "invoice.pricing.details"
    _description = "invoice Pricing Details"

    user_id = fields.Many2one('res.users', string='Users')
    inv_wiz_id = fields.Many2one('invoice.menu.wizard', string='Invoice Wizard ID')
    price = fields.Float('Unit Price')
    quantity = fields.Float('Quantity')
    emp_total_hr = fields.Float('Total Hours', readonly=True)
    is_disable = fields.Boolean('Is Disable', default=False)
    is_timesheet = fields.Boolean('Is Timesheet', default=True)
    product_id = fields.Many2one("product.product", "Product")
    invoice_line_type = fields.Selection([('employee_wise', 'Employee wise'), ('product_wise', 'Product wise')],
                                         string='Invoice line type')
    analytic_line_ids = fields.Text('Activiy Line Ids')

    # Create new pricing line and delete existing pricing line for employee
    @api.model
    def create(self, vals):
        if vals.get('invoice_line_type') == 'employee_wise':
            invoice_pricing_line_ids = self.env['invoice.pricing.details'].sudo().search(
                [('user_id', '=', vals.get("user_id")), ('inv_wiz_id', '=', vals.get("inv_wiz_id")),
                 ('product_id', '=', vals.get("product_id"))])
            if invoice_pricing_line_ids:
                for line_id in invoice_pricing_line_ids:
                    line_id.sudo().unlink()
        else:
            invoice_pricing_line_ids = self.env['invoice.pricing.details'].sudo().search(
                [('product_id', '=', vals.get("product_id")), ('inv_wiz_id', '=', vals.get("inv_wiz_id"))])
            if invoice_pricing_line_ids:
                for line_id in invoice_pricing_line_ids:
                    line_id.sudo().unlink()
        if 'user_id' not in vals and 'product_id' not in vals:
            vals = []
        return super(InvoicePricingDetails, self.sudo()).create(vals)

    @api.onchange('user_id', 'product_id')
    def onchange_add_items(self):
        timesheet_lines = None
        total = 0.0
        if self.inv_wiz_id.invoice_line_type == 'employee_wise' and self.user_id and self.product_id:
            if self.inv_wiz_id.not_approve_ts:
                timesheet_lines = self.env['account.analytic.line'].sudo().search(
                    [('date', '>=', self.inv_wiz_id.date_from), ('date', '<=', self.inv_wiz_id.date_to),
                     ('billable', '=', True),
                     ('account_id', 'in', self.inv_wiz_id.account_ids.ids), ('display_name', '=', self.user_id.id),
                     ('product_type', '=', self.product_id.id),
                     ('invoiced', '=', False)])
            else:
                timesheet_lines = self.env['account.analytic.line'].sudo().search(
                    [('date', '>=', self.inv_wiz_id.date_from), ('date', '<=', self.inv_wiz_id.date_to),
                     ('billable', '=', True),
                     ('account_id', 'in', self.inv_wiz_id.account_ids.ids), ('display_name', '=', self.user_id.id),
                     ('product_type', '=', self.product_id.id),
                     ('invoiced', '=', False), ('approved', '=', True)])
        elif self.inv_wiz_id.invoice_line_type == 'product_wise' and self.product_id and not self.emp_total_hr:
            if self.inv_wiz_id.not_approve_ts:
                timesheet_lines = self.env['account.analytic.line'].sudo().search(
                    [('date', '>=', self.inv_wiz_id.date_from), ('date', '<=', self.inv_wiz_id.date_to),
                     ('billable', '=', True),
                     ('account_id', 'in', self.inv_wiz_id.account_ids.ids), ('product_type', '=', self.product_id.id),
                     ('invoiced', '=', False)])
            else:
                timesheet_lines = self.env['account.analytic.line'].sudo().search(
                    [('date', '>=', self.inv_wiz_id.date_from), ('date', '<=', self.inv_wiz_id.date_to),
                     ('billable', '=', True),
                     ('account_id', 'in', self.inv_wiz_id.account_ids.ids), ('product_type', '=', self.product_id.id),
                     ('invoiced', '=', False), ('approved', '=', True)])

        if timesheet_lines is not None:
            for record in timesheet_lines:
                total += record.unit_amount
            self.emp_total_hr = total
            self.quantity = 1.0
