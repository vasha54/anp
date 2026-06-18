from odoo import models, fields, api

class ConfigParameterUpdate(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def update_auth_signup_parameter(self):
        """Actualiza el parámetro auth_signup.invitation_scope"""
        parameter = self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'auth_signup.invitation_scope')
        ])
        if parameter:
            parameter.write({'value': 'b2b'})
        else:
            self.create({
                'key': 'auth_signup.invitation_scope',
                'value': 'b2b'
            })
