from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True)
    product_hsn_or_sac_code = fields.Char("HSN/SAC", related="product_id.l10n_in_hsn_code")
