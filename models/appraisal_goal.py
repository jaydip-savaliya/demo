from odoo import fields, api, models
from odoo.tools import html2plaintext, is_html_empty
from odoo.exceptions import ValidationError

class HrAppraisalGoal(models.Model):
    _name = "appraisal.goal"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Appraisal Goal"

    name = fields.Char(required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee",
        default=lambda self: self.env.user.employee_id, required=True)
    manager_id = fields.Many2one('hr.employee', string="Manager", required=True)
    manager_user_id = fields.Many2one('res.users', related='manager_id.user_id')
    description = fields.Html()
    deadline = fields.Date()
    notes = fields.Html(string="Description", help="The content of this description is not visible by the Employee.")
    show_attachments = fields.Boolean(string="Show Attachments", default=False)
    attachment_file = fields.Binary(string="Attachment")
    attachment_filename = fields.Char(string="Attachment Filename")
    progression = fields.Selection(selection=[
        ('0', '0 %'),
        ('25', '25 %'),
        ('50', '50 %'),
        ('75', '75 %'),
        ('100', '100 %')
    ], string="Progress", default="0", tracking=True, required=True, copy=False)
    is_manager = fields.Boolean(string="Is Manager", compute="_compute_is_manager")

    def _compute_is_manager(self):
        for record in self:
            record.is_manager = self.env.user.has_group('aspl_hr_appraisal.group_appraisal_manager')

    def action_confirm(self):
        for record in self:
            if not record.name:
                raise ValidationError("The name field is required.")
            if not record.employee_id:
                raise ValidationError("The employee field is required.")
            if not record.manager_id:
                raise ValidationError("The manager field is required.")
            if not record.deadline:
                raise ValidationError("The deadline field is required.")
            if not record.attachment_file:
                raise ValidationError("The attachment file is required.")
        self.write({'progression': '100'})
    
