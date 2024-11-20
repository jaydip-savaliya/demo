import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class InvoiceTmplData(models.Model):
    _name = "invoice.template.data"
    _description = "invoice Template Data"

    name = fields.Char(string='Template Name')
    account_ids = fields.Many2many('account.analytic.account', 'rel_account_analytic_account_invoice_template_data',
                                   'analytic_account_ids', 'invoice_template_data_id', string='Project', store=True,
                                   help="Projects")
    partner_id = fields.Many2one('res.partner', 'Client', store=True, help="Customer")
    invoice_line_type = fields.Selection([('employee_wise', 'Employee wise'), ('product_wise', 'Product wise')],
                                         string='Invoice line type')
    date_format = fields.Many2one('invoice.date.format', string='Date Format')
    inv_wiz_id = fields.Many2one('invoice.menu.wizard', 'Invoice Pricing Details')
    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type')
    discount_rate = fields.Float('Discount Amount', digits=(16, 2))
    partner_bank_id = fields.Many2one('res.partner.bank', string="Recipient Bank Account")
    company_id = fields.Many2one('res.company', string="Company")


class InvoiceDateFormat(models.Model):
    _name = "invoice.date.format"
    _description = "invoice Date Format"

    name = fields.Char('Date Format')

    _sql_constraints = [
        ('name', 'unique(name)', ' This Date Format is already exist. Please enter unique Date Format.')
    ]

    @api.model
    def create(self, vals):
        record = super(InvoiceDateFormat, self).create(vals)
        date_list = ['m', 'mm', 'mmm', 'mmmm', 'yyyy', 'd', 'dd']
        if vals['name']:
            separator = re.split(r"[\w']+", vals['name'])
            if not separator:
                raise UserError(_('Please enter valid date format.'))

            date = re.findall(r"[\w']+", vals['name'])

            if len(date) == 1 or len(date) == 2:
                raise UserError(_('Please enter valid date format.'))

            if date[0] not in date_list or date[1] not in date_list or date[2] not in date_list:
                raise UserError(_('Please enter valid date format.'))

        return record

    def write(self, vals):
        record = super(InvoiceDateFormat, self).write(vals)
        date_list = ['m', 'mm', 'mmmm', 'mmm', 'yyyy', 'd', 'dd']

        if self.name:
            separator = re.split(r"[\w']+", self.name)
            if not separator:
                raise UserError(_('Please enter valid date format.'))

            date = re.findall(r"[\w']+", self.name)

            if len(date) == 1 or len(date) == 2:
                raise UserError(_('Please enter valid date format.'))

            if date[0] not in date_list or date[1] not in date_list or date[2] not in date_list:
                raise UserError(_('Please enter valid date format.'))

        return record
