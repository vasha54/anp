from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class RatingRating(models.Model):
    _inherit = 'rating.rating'

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for rating in self:
            if not rating.res_model:
                # Si res_model es False, None o '', asignamos nombre vacío
                rating.res_name = ''
            else:
                try:
                    Model = self.env[rating.res_model]
                    record = Model.sudo().browse(rating.res_id)
                    rating.res_name = record.display_name if record.exists() else ''
                except KeyError:
                    _logger.warning(
                        "Model %s not found for rating ID %s", rating.res_model, rating.id
                    )
                    rating.res_name = ''