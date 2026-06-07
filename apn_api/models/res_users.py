from odoo import api, fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    jwt_token = fields.Char(string="JWT Token", copy=False)
    token_expiration = fields.Datetime(string="Token Expiration", copy=False)
    
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