from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    journal_id = fields.Many2one('account.journal', string="Journal",
                                 domain="[('company_id', '=', current_company_id)]")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    journal_id = fields.Many2one("account.journal", related='company_id.journal_id', readonly=False)
