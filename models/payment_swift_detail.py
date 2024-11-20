from odoo import models, fields


class PaymentSwiftDetails(models.Model):
    _name = 'payment.swift.details'
    _description = "Payment Swift Details"
    _order = "name"

    name = fields.Char(string='Our Correspondence Bank Name', translate=True, required=True)
    our_correspondence_bank_account_no = fields.Char(string='Our Correspondence Bank A/c no.')
    our_correspondence_bank_swift_code = fields.Char(string='Our Correspondence Bank Swift Code')
    routing_no = fields.Char('ABA FED Number')
    iban_no = fields.Char('IBAN No')
    bank_clearing_code = fields.Char("Bank Clearing Code")
    currency = fields.Many2one('res.currency', "Currency", domain=[('active', '=', True)], required=True)
