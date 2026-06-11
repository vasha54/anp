from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    latitude = fields.Float(
        string="Latitude",
        digits=(16, 7),
        help="Latitude coordinate (e.g., 19.4326)"
    )
    longitude = fields.Float(
        string="Longitude",
        digits=(16, 7),
        help="Longitude coordinate (e.g., -99.1332)"
    )
    map_url = fields.Char(
        string="Map URL",
        compute='_compute_map_url'
    )
    # Relación inversa: sucursales de una compañía
    branch_ids = fields.One2many(
        'res.company',
        'parent_company_id',
        string="Branches",
        domain="[('is_branch', '=', True)]"
    )
    count_branchs = fields.Integer(
        compute='_count_branchs',
        string="Branches",
        store=False,
    )

    def create(self, vals):
        current_context = self.env.context
        return super().create(vals)

    @api.depends('latitude', 'longitude')
    def _compute_map_url(self):
        """Genera URL de Google Maps"""
        for record in self:
            if record.latitude and record.longitude:
                record.map_url = (
                    f"https://www.google.com/maps?q={record.latitude},{record.longitude}"
                )
            else:
                record.map_url = False

    def open_map(self):
        """Abre la ubicación en Google Maps"""
        self.ensure_one()
        if self.map_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.map_url,
                'target': 'new',
            }
        return False

    def geo_localize(self):
        """Geolocaliza usando la dirección existente (Google Maps API)"""
        self.ensure_one()
        # Construir dirección desde los campos existentes
        address_parts = []
        if self.street:
            address_parts.append(self.street)
        if self.city:
            address_parts.append(self.city)
        if self.state_id:
            address_parts.append(self.state_id.name)
        if self.zip:
            address_parts.append(self.zip)
        if self.country_id:
            address_parts.append(self.country_id.name)

        address = ', '.join(address_parts)

        if address:
            # Aquí puedes integrar con Google Maps Geocoding API
            # o usar el servicio de Odoo para geolocalización
            _logger.info(f"Geolocalizando dirección: {address}")
            # Ejemplo: resultado = self._call_geocoding_api(address)
            # self.latitude = resultado.lat
            # self.longitude = resultado.lng
            return True
        return False

    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        """
        Método que utiliza el geocodificador base de Odoo
        """
        geocoder = self.env['base.geocoder']
        geocoded_address = geocoder.geo_query_address(street=street, zip=zip, city=city, state=state, country=country)

        _logger.info("Geoquery address result: %s", geocoded_address)

        result = geocoder.geo_find(addr=geocoded_address)

        if not result:
            return None

        lat, long = result
        _logger.info("Geofind result: %s, %s", lat, long)

        return lat, long

    def get_distance_from(self, lat, lon):
        """Calcula distancia en km desde un punto dado"""
        self.ensure_one()
        if not self.latitude or not self.longitude:
            return None

        from math import radians, sin, cos, sqrt, atan2

        R = 6371  # Radio de la Tierra en km

        lat1 = radians(self.latitude)
        lon1 = radians(self.longitude)
        lat2 = radians(lat)
        lon2 = radians(lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    def geo_localize(self):
        """
        Método llamado desde la UI para geolocalizar una sucursal
        """
        for branch in self:
            if not branch.country_id:
                raise UserError(_("Please select a country for the branch %s", branch.name))

            result = self._geo_localize(
                street=branch.street,
                zip=branch.zip,
                city=branch.city,
                state=branch.state_id.name,
                country=branch.country_id.name
            )

            if result:
                branch.write({
                    'latitude': result[0],
                    'longitude': result[1],
                })

        return True

    @api.constrains('street', 'city', 'state_id', 'zip', 'country_id')
    def check_has_address(self):
        for record in self:
            if record.partner_id:
                entity_type = "branch" if record.is_branch else "company"
                missing_fields = []

                if not record.partner_id.street:
                    missing_fields.append("street")
                if not record.partner_id.city:
                    missing_fields.append("city")
                if not record.partner_id.state_id:
                    missing_fields.append("state")
                if not record.partner_id.zip:
                    missing_fields.append("zip code")
                if not record.partner_id.country_id:
                    missing_fields.append("country")

                if missing_fields:
                    fields_str = ", ".join(missing_fields)
                    raise UserError(
                        _("The %s is missing the following address fields: %s") % (entity_type, fields_str)
                    )

    @api.model
    def create(self, vals):
        records = super().create(vals)
        for company in records:
            company._link_admin_support_users()  # ← añade esta línea
        return records

    def _get_admin_support_group_ids(self):
        """Devuelve una tupla (id_grupo_admin, id_grupo_soporte) o (False, False) si no existen."""
        admin_group = self.env.ref('apn_group.group_admin_apn_pilates', raise_if_not_found=False)
        support_group = self.env.ref('apn_group.group_support_anp_pilates', raise_if_not_found=False)
        return (admin_group.id if admin_group else False, support_group.id if support_group else False)

    def _link_admin_support_users(self):
        """Agrega esta compañía a la lista de compañías permitidas de todos los usuarios
        que pertenecen a los grupos APN PILATES Administrator o APN PILATES Technical Support."""
        admin_id, support_id = self._get_admin_support_group_ids()
        group_ids = [gid for gid in [admin_id, support_id] if gid]
        if not group_ids:
            return
        users = self.env['res.users'].sudo().search([('groups_id', 'in', group_ids)])
        for user in users:
            if self.id not in user.company_ids.ids:
                user.sudo().write({'company_ids': [(4, self.id)]})

    @api.depends('branch_ids')
    def _count_branchs(self):
        for record in self:
            if record.branch_ids:
                record.count_branchs = len(record.branch_ids)
            else:
                record.count_branchs = 0