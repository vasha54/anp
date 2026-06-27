from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    rating_ids = fields.One2many(
        'rating.rating', 'res_id',
        domain=[('res_model', '=', 'product.template')],
        string='Ratings'
    )

    vote_count = fields.Integer(
        string="Number of Votes",
        compute="_compute_vote_stats",
        store=True,
        help="Total number of ratings with a score."
    )
    vote_average = fields.Float(
        string="Average Rating",
        compute="_compute_vote_stats",
        store=True,
        digits=(2, 1),
        help="Average of all received scores (0.0 – 5.0)."
    )
    comment_count = fields.Integer(
        string="Number of Comments",
        compute="_compute_comment_stats",
        store=True,
        help="Total number of ratings that contain a comment (feedback)."
    )
    favorite_partner_ids = fields.Many2many(
        'res.partner',
        'partner_product_tmpl_favorite_rel',  # misma tabla que en res.partner
        'product_tmpl_id',
        'partner_id',
        string='Favorited by Partners'
    )
    favorite_count = fields.Integer(
        string="Number of Favorites",
        compute="_compute_favorite_count",
        store=True,
        help="Total number of customers who have marked this template as favorite."
    )

    @api.depends('rating_ids', 'rating_ids.rating')
    def _compute_vote_stats(self):
        for product in self:
            ratings = product.rating_ids.filtered(lambda r: r.rating is not None)
            count = len(ratings)
            avg = sum(ratings.mapped('rating')) / count if count > 0 else 0.0
            product.vote_count = count
            product.vote_average = avg

    @api.depends('rating_ids.feedback')
    def _compute_comment_stats(self):
        for product in self:
            product.comment_count = len(product.rating_ids.filtered(
                lambda r: r.feedback and r.feedback.strip()
            ))

    @api.depends('favorite_partner_ids')
    def _compute_favorite_count(self):
        for product in self:
            product.favorite_count = len(product.favorite_partner_ids)
