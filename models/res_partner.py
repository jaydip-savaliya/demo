from odoo import fields, models


class res_partner(models.Model):
    _inherit = 'res.partner'

    currency = fields.Many2one('res.currency', "Currency", domain=[('active', '=', True)])
    payment_detial = fields.Many2one('payment.swift.details', "Payment Instruction",
                                     domain="[('currency', '=', currency )]")
    tax_ids = fields.Many2many('account.tax', 'partner_tax_rel', 'partner_id', 'tax_id', string='Tax')
    pan_no = fields.Char('PAN NO')
