from odoo import models, fields


class Project(models.Model):
    _inherit = 'project.project'

    product_id = fields.Many2many(comodel_name='product.product', string="Product")
