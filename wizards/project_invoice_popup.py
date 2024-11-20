# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re
from datetime import timedelta, date, datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class InvoiceMenu(models.Model):
    _name = "invoice.menu.wizard"
    _description = "invoice Menu Wizard"

    account_ids = fields.Many2many('account.analytic.account', 'rel_account_analytic_account_invoice_menu_wizard',
                                   'account_analytic_account_id', 'invoice_menu_wizard_id', string='Project',
                                   required=True, )
    date_from = fields.Date('Date from', select=1, required=True, default=lambda self: self.get_default_start_date())
    date_to = fields.Date('Date to', select=1, required=True, default=lambda self: self.get_default_end_date())
    not_approve_ts = fields.Boolean('Consider not approved Timesheet lines', default=True)
    partner_id = fields.Many2one('res.partner', 'Client', required=True, store=True)
    invoice_tmpl = fields.Many2one('invoice.template.data', 'Pre-created Invoice',
                                   help="To select previously created invoice template(s).")
    tmpl_name = fields.Char(string='New Invoice Name', required=True, store=True,
                            help="To give name to new invoice template.")
    date_format = fields.Many2one('invoice.date.format', string='Date Format', required=True)
    state = fields.Selection([('draft', 'draft'), ('invoice', 'invoice'), ('invoice2', 'invoice2')], string='State',
                             invisible=True, default='draft')
    invoice_pricing = fields.One2many('invoice.pricing.details', 'inv_wiz_id', string='Invoice Pricing Details',
                                      domain=[('is_timesheet', '=', True)])
    invoice_pricing2 = fields.One2many('invoice.pricing.details', 'inv_wiz_id', string='Invoice Pricing Details',
                                       domain=[('is_timesheet', '=', True)])
    invoice_line_type = fields.Selection([('employee_wise', 'Employee wise'), ('product_wise', 'Product wise')],
                                         string='Invoice line type')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.context['allowed_company_ids'][0])
    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], string='Discount Type',
                                     default='percent')
    discount_rate = fields.Float('Discount Amount', digits=(16, 2), default=0.00)
    partner_bank_id = fields.Many2one('res.partner.bank', string='Recipient Bank', store=True)
    gst_treatment = fields.Selection([
        ('regular', 'Registered Business - Regular'),
        ('composition', 'Registered Business - Composition'),
        ('unregistered', 'Unregistered Business'),
        ('consumer', 'Consumer'),
        ('overseas', 'Overseas'),
        ('special_economic_zone', 'Special Economic Zone'),
        ('deemed_export', 'Deemed Export')
    ], string="GST Treatment", store=True, readonly=False, default='consumer', required=True)

    @api.onchange('company_id')
    def _get_currency_company_banks(self):
        if self.company_id:
            return {"domain": {'partner_bank_id': [('partner_id.name', '=', self.company_id.name)]}}

    # provide Start date to wizard
    def get_default_start_date(self):
        today = datetime.now()
        current_month_start = today.replace(day=1)
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        return prev_month_start

    # provide End date to wizard
    def get_default_end_date(self):
        today = datetime.now()
        current_month_start = today.replace(day=1)
        prev_month_end = current_month_start - timedelta(days=1)

        return prev_month_end

    def action_previous_state(self):
        self.write({'state': 'draft'})
        # return view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.menu.wizard',
            'name': "Generate Invoice",
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
            'view_id': self.id,
        }

    def enter_pricing_timesheet_invoice(self):

        if self.invoice_line_type == 'employee_wise':
            invoice_pricing_ids = self.env['invoice.pricing.details'].sudo().search(
                [('inv_wiz_id', '=', self.id), ('invoice_line_type', '=', 'employee_wise')])
            self.state = 'invoice'  # Update the state value from draft to invoice.

            if self.not_approve_ts:
                query = "SELECT display_name , sum(unit_amount),product_type FROM public.account_analytic_line where date >= '" + str(
                    self.date_from) + "' and date <= '" + str(self.date_to) + "' and account_id in " + str(
                    self.account_ids.ids).replace("[", "(").replace("]",
                                                                    ")") + " and billable = True and (invoiced != True or invoiced is null) and product_type is not null and unit_amount > '00.00' group by display_name,product_type;"
            else:
                query = "SELECT display_name , sum(unit_amount),product_type FROM public.account_analytic_line where date >= '" + str(
                    self.date_from) + "' and date <= '" + str(self.date_to) + "' and account_id in " + str(
                    self.account_ids.ids).replace("[", "(").replace("]",
                                                                    ")") + " and billable = True and Approved = True and product_type is not null and (invoiced != True or invoiced is null) and unit_amount > '00.00' group by display_name,product_type;"

            # fetch pricing details based on selected invoice template.
            self.env.cr.execute(query)
            row = self.env.cr.fetchone()
            data = []
            user_list = []
            while row is not None:
                d = [row[var] for var in range(len(row))]
                data.append(d)
                user_list.append(d[0])
                row = self.env.cr.fetchone()

            if data:
                inv_price_obj = self.env['invoice.pricing.details']

                price_line_list = []
                for user in data:
                    user_price_line = inv_price_obj.sudo().search(
                        [('inv_wiz_id', '=', self.invoice_tmpl.inv_wiz_id.id), ('inv_wiz_id', '!=', False),
                         ('invoice_line_type', '=', 'employee_wise'), ('user_id', '=', user[0]),
                         ('product_id', '=', user[2])])
                    price_line_list.append(user_price_line.id)

                if len(price_line_list) > 1:
                    pricing_ids = inv_price_obj.browse(price_line_list[0])
                else:
                    pricing_ids = inv_price_obj.browse(price_line_list)

                self.invoice_pricing = pricing_ids

                if pricing_ids:
                    self.invoice_tmpl.inv_wiz_id = self.id

                for pricing_id in pricing_ids:
                    pricing_id.write({
                        'inv_wiz_id': self.id
                    })

                # Added code to pre-fill pricing details for new record.
                for user_data in data:
                    emp_price_line_id = inv_price_obj.sudo().search(
                        [('inv_wiz_id', '=', self.invoice_tmpl.inv_wiz_id.id), ('inv_wiz_id', '!=', False),
                         ('invoice_line_type', '=', 'employee_wise'), ('user_id', '=', user_data[0]),
                         ('product_id', '=', user_data[2])])

                    if emp_price_line_id:
                        emp_price_line_id.write({'emp_total_hr': user_data[1]})
                    else:
                        self.pre_fill_pricing_details(user_data, inv_price_obj)

                # Added code to fill up previous wizard id in pricing and template data.
                invoice_templates = self.env['invoice.template.data'].search([('inv_wiz_id', '=', self.id)])
                for inv_tmpl in invoice_templates:
                    if self.invoice_tmpl.id != inv_tmpl.id:
                        pre_invoice_wiz_id = self.sudo().search([('invoice_tmpl', '=', inv_tmpl.id)], order="id desc",
                                                                limit=1)
                        inv_tmpl.sudo().write({'inv_wiz_id': pre_invoice_wiz_id.id})
                        invoice_pricing_ids.sudo().write({'inv_wiz_id': pre_invoice_wiz_id.id})
            else:
                raise UserError(
                    "No analytic lines to create invoiceSorry! No Timesheet lines are found for the project to Invoice.")
        else:

            if self.not_approve_ts:
                query = "SELECT product_type , sum(unit_amount),string_agg( CAST(id as varchar(25)),',') FROM public.account_analytic_line where date >= '" + str(
                    self.date_from) + "' and date <= '" + str(self.date_to) + "' and account_id in " + str(
                    self.account_ids.ids).replace("[", "(").replace("]",
                                                                    ")") + " and billable = True and product_type is not null and (invoiced != True or invoiced is null) and unit_amount > '00.00' group by product_type;"
            else:
                query = "SELECT product_type , sum(unit_amount),string_agg( CAST(id as varchar(25)),',') FROM public.account_analytic_line where date >= '" + str(
                    self.date_from) + "' and date <= '" + str(self.date_to) + "' and account_id in " + str(
                    self.account_ids.ids).replace("[", "(").replace("]",
                                                                    ")") + " and billable = True  and (invoiced != True or invoiced is null) and product_type is not null and Approved = True and unit_amount > '00.00' group by product_type;"

            # fetch pricing details based on selected invoice template.
            self.env.cr.execute(query)
            row = self.env.cr.fetchone()
            data = []
            product_list = []
            while row is not None:
                d = [row[var] for var in range(len(row))]
                data.append(d)
                product_list.append(d[0])
                row = self.env.cr.fetchone()
            if data:
                invoice_pricing_ids = self.env['invoice.pricing.details'].sudo().search(
                    [('inv_wiz_id', '=', self.invoice_tmpl.inv_wiz_id.id), ('invoice_line_type', '=', 'product_wise')])
                self.state = 'invoice2'  # Update the state value from draft to invoice.

                # fetch pricing details based on selected invoice template.
                inv_price_obj = self.env['invoice.pricing.details']
                pricing_line_ids = inv_price_obj.sudo().search(
                    [('inv_wiz_id', '=', self.invoice_tmpl.inv_wiz_id.id), ('inv_wiz_id', '!=', False),
                     ('invoice_line_type', '=', 'product_wise'), ('product_id', 'in', product_list)])
                line_ids = []
                product_ids = []
                for price_line in pricing_line_ids:
                    if price_line.product_id.id not in product_ids:
                        product_ids.append(price_line.product_id.id)
                        line_ids.append(price_line.id)

                pricing_ids = inv_price_obj.browse(line_ids)

                self.invoice_pricing2 = pricing_ids

                if pricing_ids:
                    self.invoice_tmpl.inv_wiz_id = self.id
                    for pricing_id in pricing_ids:
                        pricing_id.write({
                            'inv_wiz_id': self.id
                        })
                for product_data in data:
                    product_price_line_id = inv_price_obj.sudo().search(
                        [('inv_wiz_id', '=', self.invoice_tmpl.inv_wiz_id.id), ('inv_wiz_id', '!=', False),
                         ('invoice_line_type', '=', 'product_wise'), ('product_id', '=', product_data[0])])
                    if product_price_line_id:
                        product_price_line_id.write({'emp_total_hr': product_data[1],
                                                     'analytic_line_ids': product_data[2]})
                    else:
                        self.pre_fill_pricing_details_product(product_data, inv_price_obj)
            else:
                raise UserError("Sorry! No Timesheet lines are found for the project to Invoice.")

        return {
            'res_model': 'invoice.menu.wizard',
            'view_mode': 'form',
            'name': "Generate Invoice",
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def onchange_date_format(self):
        date_list = []
        date_format = self.date_format.name
        date_format = str(date_format)
        if date_format != 'False':
            separator = re.split(r"[\w']+", date_format)  # Split separator from date format
            date = re.findall(r"[\w']+", date_format)  # Split month,day and year from date format

            # Append month,day and year in date_list
            date_list.append(date[0])
            date_list.append(date[1])
            date_list.append(date[2])

            # Replace month/day/year to display date as per python date strftime date format
            temp_date_list = [list.replace('mmmm', 'B') for list in date_list]
            temp_date_list1 = [list.replace('mmm', 'b') for list in temp_date_list]
            temp_date_list2 = [list.replace('m', '-m') for list in temp_date_list1]
            temp_date_list3 = [list.replace('mm', 'm') for list in temp_date_list2]
            temp_date_list4 = [list.replace('d', '-d') for list in temp_date_list3]
            temp_date_list5 = [list.replace('dd', 'd') for list in temp_date_list4]
            temp_date_list6 = [list.replace('-d-d', 'd') for list in temp_date_list5]
            temp_date_list7 = [list.replace('-m-m', 'm') for list in temp_date_list6]
            final_date_list = [list.replace('yyyy', 'Y') for list in temp_date_list7]

            inv_date_format = '%' + final_date_list[0] + separator[1] + '%' + final_date_list[1] + separator[2] + '%' + \
                              final_date_list[2]

            return inv_date_format

    @api.onchange('invoice_tmpl')
    def _onchange_inv_wiz_data(self):
        self.partner_id = self.invoice_tmpl.partner_id
        self.invoice_line_type = self.invoice_tmpl.invoice_line_type
        self.account_ids = self.invoice_tmpl.account_ids
        self.tmpl_name = self.invoice_tmpl.name
        self.invoice_line_type = self.invoice_tmpl.invoice_line_type
        self.partner_bank_id = self.invoice_tmpl.partner_bank_id
        self.date_format = self.invoice_tmpl.date_format
        self.discount_rate = self.invoice_tmpl.discount_rate
        self.discount_type = self.invoice_tmpl.discount_type
        self.company_id = self.invoice_tmpl.company_id if self.invoice_tmpl.company_id else self.env.company.id

    @api.model
    def pre_fill_pricing_details(self, user_data, inv_price_obj):
        '''
        Added code to pre-fill pricing details for new record.
        '''


        if user_data[2]:
            id_data = inv_price_obj.sudo().create({
                'inv_wiz_id': self.id,
                'user_id': user_data[0],
                'price': 0,
                'product_id': user_data[2],
                'emp_total_hr': user_data[1],
                'invoice_line_type': self.invoice_line_type,
            })
        else:
            raise UserError("Please! Add Product In Timesheet Entry From " + str(
                datetime.strptime(str(self.date_from), '%Y-%m-%d').strftime('%d/%m/%Y')) + " to " + str(
                datetime.strptime(str(self.date_to), '%Y-%m-%d').strftime('%d/%m/%Y')))

    @api.model
    def pre_fill_pricing_details_product(self, product_data, inv_price_obj):
        if product_data[0]:

            inv_price_obj.create({
                'inv_wiz_id': self.id,
                'price': 0,
                'quantity': 1,
                'product_id': product_data[0],
                'emp_total_hr': product_data[1],
                'invoice_line_type': self.invoice_line_type,
                'analytic_line_ids': str(product_data[2])
            })
        else:
            raise UserError("Please! Add Product In Timesheet Entry From " + str(
                datetime.strptime(str(self.date_from), '%Y-%m-%d').strftime('%d/%m/%Y')) + " to " + str(
                datetime.strptime(str(self.date_to), '%Y-%m-%d').strftime('%d/%m/%Y')))

    def create_invoice(self):
        invoice_id = None
        inv_date_format = self.onchange_date_format()
        journal_id = self.company_id.journal_id
        if not journal_id:
            raise UserError("Please configure 'journal' in project setting.")
        if not self.partner_id.currency:
            raise UserError("Please set 'Currency' in the customer.")
        elif not self.partner_id.payment_detial:
            raise UserError("Please add 'Payment Swift Details' in the customer.")
        elif not self.partner_id.property_account_receivable_id:
            raise UserError("Please set 'Accounts' in the customer.")
        elif not self.partner_id.property_payment_term_id:
            raise UserError("Please set 'Payment Terms' in the customer.")
        else:
            try:
                invoice_id = self.env['account.move'].create({
                    'partner_id': self.partner_id.id,
                    'currency_id': self.partner_id.currency.id,
                    'invoice_date': date.today(),
                    'payment_swift_id': self.partner_id.payment_detial.id,
                    'move_type': 'out_invoice',
                    'l10n_in_gst_treatment': self.partner_id.l10n_in_gst_treatment,
                    'partner_bank_id': self.partner_bank_id.id,
                    'company_id': self.company_id.id,
                    'invoice_payment_term_id': self.partner_id.property_payment_term_id.id,
                    'discount_type': self.discount_type,
                    'discount_rate': self.discount_rate,
                    'date_format': inv_date_format,
                    'journal_id': journal_id.id,
                })
            except Exception as e:
                _logger.error(str(e))

            return invoice_id

    def create_invoices(self):
        need_to_remove_price_list = []
        invoice_pricing_details = self.env['invoice.pricing.details']
        invoice_pricing_ids = invoice_pricing_details.sudo().search(
            [('inv_wiz_id', '=', self.id), ('is_disable', '=', False)])
        project_data = None
        product_list = []
        for price_lines in invoice_pricing_ids:
            if self.invoice_line_type == "product_wise":
                if price_lines.product_id not in product_list:
                    product_list.append(price_lines.product_id)
                    price_lines.write({
                        'inv_wiz_id': self.id
                    })
                else:
                    need_to_remove_price_list.append(price_lines.id)
                    continue

        if not need_to_remove_price_list:
            invoice = self.create_invoice()
            for price_lines in invoice_pricing_ids:
                if price_lines.analytic_line_ids:
                    update_product_query = "UPDATE public.account_analytic_line SET product_type=" + str(
                        price_lines.product_id.id) + " WHERE  id in (" + price_lines.analytic_line_ids + ");"
                    self.env.cr.execute(update_product_query)
        else:
            return {
                'name': 'confirmation',
                'type': 'ir.actions.act_window',
                'res_model': 'confirm.wizard',
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'need_to_remove_price_list': need_to_remove_price_list}
            }

        if invoice:
            discount = self.discount_count(invoice_pricing_ids)

            for price_lines in invoice_pricing_ids:
                create_invoice_line = None

                if price_lines.invoice_line_type == "employee_wise":
                    self.env.cr.execute(
                        "SELECT DISTINCT account_id FROM public.account_analytic_line where display_name = " + str(
                            price_lines.user_id.id) + " and product_type = " + str(price_lines.product_id.id) + ";")
                    row = self.env.cr.fetchone()
                    project_data = self.env['project.project'].sudo().search(
                        [('analytic_account_id', 'in', [row[var] for var in range(len(row))])])
                product_id = price_lines.product_id.id
                product_hsn_or_sac_code = price_lines.product_id.l10n_in_hsn_code
                price_unit = price_lines.price
                if not price_lines.product_id.property_account_income_id:
                    raise UserError("Please set 'Income Accounts' in the product.")
                else:
                    account_id = price_lines.product_id.property_account_income_id
                invoice_id = invoice.id

                if self.invoice_line_type == 'employee_wise':
                    if self.not_approve_ts:
                        timesheet_lines = self.env['account.analytic.line'].sudo().search(
                            [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('billable', '=', True),
                             ('account_id', 'in', self.account_ids.ids), ('display_name', '=', price_lines.user_id.id),
                             ('invoiced', '=', False), ('product_type', '=', price_lines.product_id.id)])
                    else:
                        timesheet_lines = self.env['account.analytic.line'].sudo().search(
                            [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('billable', '=', True),
                             ('account_id', 'in', self.account_ids.ids), ('display_name', '=', price_lines.user_id.id),
                             ('invoiced', '=', False), ('approved', '=', True),
                             ('product_type', '=', price_lines.product_id.id)])

                    tempComment = 'Software Consultancy Services provided by ' + str(
                        price_lines.user_id.name) + ' ' + str('on') + ' ' + str(project_data.name) + ' ' + str(
                        'from') + ' ' + str(datetime.strptime(str(self.date_from), '%Y-%m-%d').strftime(
                        invoice.date_format)) + ' to ' + str(
                        datetime.strptime(str(self.date_to), '%Y-%m-%d').strftime(invoice.date_format))
                    time = price_lines.emp_total_hr
                else:
                    if self.not_approve_ts:
                        timesheet_lines = self.env['account.analytic.line'].sudo().search(
                            [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('billable', '=', True),
                             ('account_id', 'in', self.account_ids.ids),
                             ('product_type', '=', price_lines.product_id.id),
                             ('invoiced', '=', False)])
                    else:
                        timesheet_lines = self.env['account.analytic.line'].sudo().search(
                            [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('billable', '=', True),
                             ('account_id', 'in', self.account_ids.ids),
                             ('product_type', '=', price_lines.product_id.id),
                             ('invoiced', '=', False), ('approved', '=', True)])

                    tempComment = 'Software Consultancy Services provided from ' + str(
                        datetime.strptime(str(self.date_from), '%Y-%m-%d').strftime(
                            invoice.date_format)) + ' to ' + str(
                        datetime.strptime(str(self.date_to), '%Y-%m-%d').strftime(invoice.date_format)) + ' - ' + str(
                        price_lines.product_id.name)
                    time = price_lines.quantity

                try:
                    create_invoice_line = invoice.write({
                        'invoice_line_ids': [(0, 0, {
                            'product_id': product_id,
                            'product_hsn_or_sac_code': product_hsn_or_sac_code,
                            'price_unit': price_unit,
                            'account_id': account_id.id,
                            'quantity': time,
                            'name': tempComment,
                            'move_id': invoice_id,
                            'tax_ids': [(6, 0, [tax.id for tax in self.partner_id.tax_ids])],
                            'discount': discount,
                        })]
                    })
                    invoice._supply_rate()

                except Exception as e:
                    _logger.error(str(e))

                # To create tax line on the basis of selected customer in invoice.
                invoice_line_tax_vals = {}
                if invoice.invoice_line_ids and invoice.invoice_line_ids.tax_ids:
                    for tax_line_id in invoice.invoice_line_ids.tax_ids:
                        try:
                            invoice_line_tax_vals.sudo().update({
                                'account_id': invoice.type in ('out_invoice', 'in_invoice') and (
                                        tax_line_id.account_id.id or create_invoice_line.account_id.id) or (tax[
                                                                                                                'refund_account_id'] or create_invoice_line.account_id.id),
                                'sequence': tax_line_id.sequence,
                                'invoice_id': invoice.id,
                                'amount': (invoice.invoice_line_ids.original_amount * tax_line_id.amount) / 100,
                                'tax_id': tax_line_id.id,
                                'name': tax_line_id.name,
                            })
                            test = (invoice.amount_untaxed * tax_line_id.amount) / 100
                            create_tax_line = self.env['account.invoice.tax'].create(invoice_line_tax_vals)
                        except Exception as e:
                            _logger.error(str(e))

                # self.add_discount(invoice)
                for lines in timesheet_lines:
                    lines.sudo().write({'invoiced': True, 'invoice_id': invoice_id})

            vals = {}
            vals.update({
                'partner_id': self.partner_id.id,
                'name': self.tmpl_name,
                'invoice_line_type': self.invoice_line_type,
                'date_format': self.date_format.id,
                'discount_rate': self.discount_rate,
                'discount_type': self.discount_type,
                'partner_bank_id': self.partner_bank_id.id,
                'company_id': self.company_id.id,
                # 'gst_treatment': self.gst_treatment,
            })
            vals.update(account_ids=[(6, 0, [project.id for project in self.account_ids])])
            # To store invoice wizard id in template for pricing details reference.
            for inv_pricing_ids in invoice_pricing_ids:
                inv_pricing_id = self.env['invoice.pricing.details'].sudo().browse(
                    inv_pricing_ids.id)
                vals.update({
                    'inv_wiz_id': inv_pricing_id.inv_wiz_id.id
                })

            if self.invoice_tmpl:
                self.invoice_tmpl.sudo().write(vals)  # Update existing template if exist
            else:
                self.invoice_tmpl.create(vals)  # Create new invoice template

            self.env.cr.execute("DELETE FROM public.invoice_pricing_details WHERE inv_wiz_id is null;")

        def get_view_id(xid, name):
            try:
                return self.env.ref('account.' + xid)
            except ValueError:
                view = self.env['ir.ui.view'].search([('name', '=', name)], limit=1)
                if not view:
                    return False
                return view.id

        if invoice:
            return {
                'name': _('Invoices'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_id': get_view_id('view_move_form', 'account.move.form').id
            }

    def discount_count(self, invoice_pricing_ids):
        total = 0.0
        for price_line in invoice_pricing_ids:
            current_total = price_line.emp_total_hr * price_line.price
            total += current_total

        if self.discount_type == 'percent':
            return self.discount_rate
        else:
            return ((self.discount_rate / total) * 100)
