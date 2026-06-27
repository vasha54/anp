from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    favorite_product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        relation='partner_product_tmpl_favorite_rel',
        column1='partner_id',
        column2='product_tmpl_id',
        string='Favorite Product Templates'
    )

    favorite_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='partner_product_variant_favorite_rel',
        column1='partner_id',
        column2='product_id',
        string='Favorite Product Variants'
    )