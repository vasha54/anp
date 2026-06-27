from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nearby_branches_default_distance_meters = fields.Integer(
        string="Default distance for nearby branches (meters)",
        config_parameter='apn_company.nearby_branches_default_distance_meters',
        default=400,
        help="Maximum distance in meters to consider a branch as nearby"
    )