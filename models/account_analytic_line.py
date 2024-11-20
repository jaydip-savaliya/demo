from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _get_project_product(self):
        context = self._context

        if 'active_id' in context:
            project = context['active_id']
            project_id = self.env['project.project'].browse(project)
            domain = [('id', 'in', project_id.product_id.ids)]

        else:
            domain = [('id', 'in', [])]

        return domain

    def _set_default_product(self):
        context = self._context
        account_line = context.get('json_data')

        if account_line and 'params' in account_line and len(account_line['params'].get('args',[])) > 1:
            args = account_line['params']['args']
            if 'task_id' in ['args'][1]:
                current_uid = context.get('uid')
                task_id = args[1]['task_id']['id']

                if task_id:
                    analytic_line = self.env['account.analytic.line'].search(
                        [('task_id', '=', task_id), ('user_id', '=', current_uid)], limit=1, order='id desc')
                    if analytic_line.product_type:
                        return analytic_line.product_type.id
                    project_id = context.get('default_project_id')
                    if project_id:
                        project_line = self.env['account.analytic.line'].search(
                            [('task_id.project_id', '=', project_id), ('user_id', '=', current_uid)], limit=1,
                            order='id desc')
                        if project_line.product_type:
                            return project_line.product_type.id
                        else:
                            project = self.env['project.project'].browse(project_id)
                            product = project.product_id
                            return product.ids[0] if product else ''

                elif 'default_project_id' in context:
                    project_id = context['default_project_id']
                    project_line = self.env['account.analytic.line'].search(
                        [('task_id.project_id', '=', project_id), ('user_id', '=', current_uid)],
                        limit=1,
                        order='id desc'
                    )
                    if project_line.product_type:
                        return project_line.product_type.id
                    else:
                        project = self.env['project.project'].browse(project_id)
                        product = project.product_id
                        return product.ids[0] if product else ''

        return ''

    billable = fields.Boolean('Billable', default=True)
    invoiced = fields.Boolean('Invoiced')
    approved = fields.Boolean('Approved')
    invoice_id = fields.Many2one('account.move')
    product_type = fields.Many2one("product.product", domain=_get_project_product, string="Product",
                                   default=lambda self: self._set_default_product())
    user_id = fields.Many2one('res.users', string='User')
    # display_name = fields.Many2one('res.users', 'Display Name', default=lambda self: self.env.user)
    name = fields.Text('Description')

    @api.onchange('project_id')
    def get_default_product_type(self):
        product_id = self.project_id.product_id
        if product_id:
            return {"domain": {'product_type': [('id', 'in', self.project_id.product_id.ids)]}}

    def action_timesheet_approve(self):
        for analytic_line in self:
            analytic_line.write({
                'approved': True
            })

    def action_update_product(self):
        project_id = []
        for analytic_line in self:
            if analytic_line.project_id.id not in project_id:
                project_id.append(analytic_line.project_id.id)

        if len(project_id) > 1:
            raise ValidationError(_('Please confirm ! project must be same.'))

        if self.project_id.product_id.ids:
            product_id = self.project_id.product_id.ids
        else:
            raise ValidationError(_("Kindly add 'Product' in " + self.project_id.name + " project."))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'timesheet.product.change',
            'context': {'product_id': product_id, 'account_analytic_ids': self.ids},
            'view_mode': 'form',
            'name': _('Timesheet Product Change'),
            'target': 'new',
        }
