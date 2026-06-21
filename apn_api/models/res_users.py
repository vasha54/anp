from odoo import api, fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    jwt_token = fields.Char(string="JWT Token", copy=False)
    token_expiration = fields.Datetime(string="Token Expiration", copy=False)
    apn_groups = fields.Json(
        string="APN Groups",
        compute="_compute_apn_groups",
        store=False
    )
    partner = fields.Json(
        string="Partner",
        compute="_compute_partner",
        store=False
    )
    
    @api.model
    def _clear_expired_tokens(self):
        """ Limpia los tokens expirados (token_expiration anterior a la fecha actual) """
        now = fields.Datetime.now()
        expired_users = self.search([
            ('token_expiration', '<', now),
            ('jwt_token', '!=', False)
        ])
        expired_users.write({
            'jwt_token': False,
            'token_expiration': False
        })

    def _compute_apn_groups(self):
        for user in self:
            if user.apn_group_ids:
                groups = []
                for group in user.apn_group_ids:
                    groups.append({
                        'id': group.id,
                        'name': group.name,
                    })
                user.apn_groups = groups
            else:
                user.apn_groups = None

    def _compute_partner(self):
        for user in self:
            if user.partner_id:
                user.partner = user.partner_id.read(['id', 'name'])
            else:
                user.partner = None