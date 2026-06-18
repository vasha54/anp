from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_apn_category = fields.Boolean(
        string="Is APN Category",
        default=False,
    )

    @api.model
    def create(self, vals):
        current_context = self.env.context
        if current_context.get('apn_category'):
            vals['is_apn_category'] = True
        records = super().create(vals)
        return records