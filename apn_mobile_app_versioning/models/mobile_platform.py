from odoo import models, fields, api


class MobilePlatform(models.Model):
    _name = 'mobile.platform'
    _description = 'Mobile Platform'
    _order = 'name'

    name = fields.Char(string='Platform Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True, help='Código interno (ej: ios, android, huawei)')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'El código de la plataforma debe ser único.')
    ]

    @api.model
    def get_platforms(self):
        """
        Método RPC para obtener todas las plataformas.
        """
        platforms = self.search([])
        return [{
            'id': p.id,
            'name': p.name,
            'code': p.code,
            'active': p.active,
        } for p in platforms]