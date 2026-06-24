from odoo import models, fields, api, _


class MobileVersion(models.Model):
    _name = 'mobile.version'
    _description = 'Mobile App Version'
    _order = 'release_date desc, version desc'

    version = fields.Char(string='Version', required=True)
    platform_id = fields.Many2one('mobile.platform', string='Platform', required=True)
    release_date = fields.Date(string='Release Date', required=True, default=fields.Date.today)
    download_url = fields.Char(string='Download URL', required=True)
    is_mandatory = fields.Boolean(string='Is Mandatory?', default=False,
                                  help='Si está marcado, la app forzará la actualización.')
    release_notes = fields.Html(string='Release Notes', sanitize=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, domain=[('is_branch', '=', False)])

    @api.depends('version', 'platform_id')
    def _compute_display_name(self):
        for rec in self:
            if rec.version and rec.platform_id and rec.company_id:
                rec.display_name = f"{rec.company_id.display_name} - {rec.platform_id.name} v{rec.version}"
            elif not rec.version and rec.platform_id and rec.company_id:
                rec.display_name = f"{rec.company_id.display_name} - {rec.platform_id.name}"
            else:
                rec.display_name = _("Unknown")

    @api.model
    def get_versions(self, platform_code=None):
        """
        Método RPC para obtener versiones.
        Si platform_code es None, devuelve todas.
        Si se proporciona, filtra por el código de plataforma.
        """
        domain = []
        if platform_code:
            platform = self.env['mobile.platform'].search([('code', '=', platform_code)], limit=1)
            if platform:
                domain.append(('platform_id', '=', platform.id))
            else:
                # Si no existe la plataforma, devolver lista vacía
                return []
        versions = self.search(domain)
        # Devolver lista de diccionarios con los campos relevantes
        return [{
            'id': v.id,
            'version': v.version,
            'platform_id': v.platform_id.id,
            'platform_code': v.platform_id.code,
            'platform_name': v.platform_id.name,
            'release_date': v.release_date.isoformat() if v.release_date else None,
            'download_url': v.download_url,
            'is_mandatory': v.is_mandatory,
            'release_notes': v.release_notes,
            'display_name': v.display_name,
            'company':{
                'id': v.company_id.id,
                'name': v.company_id.name,
            }
        } for v in versions]

    @api.model
    def get_latest_version(self, platform_code):
        """
        Método RPC para obtener la última versión (por fecha) de una plataforma.
        Retorna un diccionario con los datos de la versión, o {} si no existe.
        """
        platform = self.env['mobile.platform'].search([('code', '=', platform_code)], limit=1)
        if not platform:
            return {}
        version = self.search(
            [('platform_id', '=', platform.id)],
            order='release_date desc, version desc',
            limit=1
        )
        if not version:
            return {}
        return {
            'id': version.id,
            'version': version.version,
            'release_date': version.release_date.isoformat() if version.release_date else None,
            'download_url': version.download_url,
            'is_mandatory': version.is_mandatory,
            'release_notes': version.release_notes,
            'platform_code': platform.code,
            'platform_name': platform.name,
        }

    @api.model
    def get_versions_by_company(self, company_id):
        """
        Obtiene todas las versiones para una compañía determinada.
        :param company_id: ID de la compañía (res.company)
        :return: lista de diccionarios con los datos de cada versión
        """
        versions = self.search([('company_id', '=', int(company_id))])
        return [{
            'id': v.id,
            'version': v.version,
            'platform_id': v.platform_id.id,
            'platform_code': v.platform_id.code,
            'platform_name': v.platform_id.name,
            'release_date': v.release_date.isoformat() if v.release_date else None,
            'download_url': v.download_url,
            'is_mandatory': v.is_mandatory,
            'release_notes': v.release_notes,
            'display_name': v.display_name,
            'company': {
                'id': v.company_id.id,
                'name': v.company_id.name,
            }
        } for v in versions]

    @api.model
    def get_versions_by_company_and_platform(self, company_id, platform_code):
        """
        Obtiene todas las versiones para una compañía y plataforma específicas.
        :param company_id: ID de la compañía
        :param platform_code: código de la plataforma (mobile.platform.code)
        :return: lista de diccionarios con los datos de cada versión
        """
        platform = self.env['mobile.platform'].search([('code', '=', platform_code)], limit=1)
        if not platform:
            return []
        versions = self.search([
            ('company_id', '=', int(company_id)),
            ('platform_id', '=', platform.id)
        ])
        return [{
            'id': v.id,
            'version': v.version,
            'platform_id': v.platform_id.id,
            'platform_code': v.platform_id.code,
            'platform_name': v.platform_id.name,
            'release_date': v.release_date.isoformat() if v.release_date else None,
            'download_url': v.download_url,
            'is_mandatory': v.is_mandatory,
            'release_notes': v.release_notes,
            'display_name': v.display_name,
            'company': {
                'id': v.company_id.id,
                'name': v.company_id.name,
            }
        } for v in versions]

    @api.model
    def get_latest_versions_by_company(self, company_id):
        """
        Obtiene la última versión (por fecha y versión) de cada plataforma para una compañía.
        :param company_id: ID de la compañía
        :return: lista de diccionarios, uno por cada plataforma con la última versión
        """
        # Obtener todas las versiones de la compañía, ordenadas por plataforma y fecha/versión descendente
        versions = self.search(
            [('company_id', '=', int(company_id))],
            order='platform_id, release_date desc, version desc'
        )
        # Agrupar la primera de cada plataforma
        latest_by_platform = {}
        for v in versions:
            if v.platform_id.id not in latest_by_platform:
                latest_by_platform[v.platform_id.id] = v
        # Convertir a lista de diccionarios
        result = []
        for v in latest_by_platform.values():
            result.append({
                'id': v.id,
                'version': v.version,
                'platform_id': v.platform_id.id,
                'platform_code': v.platform_id.code,
                'platform_name': v.platform_id.name,
                'release_date': v.release_date.isoformat() if v.release_date else None,
                'download_url': v.download_url,
                'is_mandatory': v.is_mandatory,
                'release_notes': v.release_notes,
                'display_name': v.display_name,
                'company': {
                    'id': v.company_id.id,
                    'name': v.company_id.name,
                }
            })
        return result

    @api.model
    def get_latest_version_by_company_and_platform(self, company_id, platform_code):
        """
        Obtiene la última versión de una plataforma específica para una compañía.
        :param company_id: ID de la compañía
        :param platform_code: código de la plataforma
        :return: diccionario con los datos de la última versión, o {} si no existe
        """
        platform = self.env['mobile.platform'].search([('code', '=', platform_code)], limit=1)
        if not platform:
            return {}
        version = self.search(
            [('company_id', '=', int(company_id)), ('platform_id', '=', platform.id)],
            order='release_date desc, version desc',
            limit=1
        )
        if not version:
            return {}
        return {
            'id': version.id,
            'version': version.version,
            'release_date': version.release_date.isoformat() if version.release_date else None,
            'download_url': version.download_url,
            'is_mandatory': version.is_mandatory,
            'release_notes': version.release_notes,
            'platform_code': platform.code,
            'platform_name': platform.name,
            'company': {
                'id': version.company_id.id,
                'name': version.company_id.name,
            }
        }