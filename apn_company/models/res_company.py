from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = "res.company"

    is_branch = fields.Boolean(string="Is Branch", default=False)
    parent_company_id = fields.Many2one(
        'res.company',
        string="Parent Company",
        help="Parent company for consolidation",
        domain = [('is_branch', '=', False)]
    )
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
    reference = fields.Char(
        string="Reference",
        help="Nearby landmarks or references"
    )
    # Relación inversa: sucursales de una compañía
    branch_ids = fields.One2many(
        'res.company',
        'parent_company_id',
        string="Branches",
        domain="[('is_branch', '=', True)]"
    )

    schedule_ids = fields.Many2many(
        comodel_name="branch.schedule",
        relation="branch_schedule_res_company_rel",
        column1="branch_id",
        column2="schedule_id",
        string="Work Schedules",
    )

    @api.constrains("schedule_ids", "is_branch")
    def _check_branch_schedules_no_overlap(self):
        """Valida que una sucursal no tenga horarios solapados"""
        for company in self:
            if not company.is_branch:
                continue

            active_schedules = company.schedule_ids.filtered(
                lambda s: s.active
            )

            # Comparar cada par de horarios
            for i, schedule1 in enumerate(active_schedules):
                for schedule2 in active_schedules[i + 1:]:
                    # Verificar solapamiento de días
                    days_overlap = self.env["apn.branch.schedule"]._days_overlap(
                        schedule1.day_of_week_from,
                        schedule1.day_of_week_to,
                        schedule2.day_of_week_from,
                        schedule2.day_of_week_to,
                    )

                    # Verificar solapamiento de horas
                    hours_overlap = self.env["apn.branch.schedule"]._hours_overlap(
                        schedule1.hour_from,
                        schedule1.hour_to,
                        schedule2.hour_from,
                        schedule2.hour_to,
                    )

                    if days_overlap and hours_overlap:
                        raise ValidationError(_(
                            "The branch '%(branch)s' has overlapping schedules:\n"
                            "• %(schedule1)s\n"
                            "• %(schedule2)s\n\n"
                            "Please adjust the schedules to avoid conflicts."
                        ) % {
                                                  "branch": company.name,
                                                  "schedule1": schedule1.display_name,
                                                  "schedule2": schedule2.display_name,
                                              })

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

        logger.info("Geoquery address result: %s", geocoded_address)

        result = geocoder.geo_find(addr=geocoded_address)

        if not result:
            return None

        lat, long = result
        logger.info("Geofind result: %s, %s", lat, long)

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

    @api.constrains('street', 'street2', 'city', 'state_id', 'zip', 'country_id')
    def check_has_address(self):
        for record in self:
            if record.partner_id:
                entity_type = "branch" if record.is_branch else "company"
                missing_fields = []

                if not record.partner_id.street:
                    missing_fields.append("street")
                if not record.partner_id.street2:
                    missing_fields.append("street2")
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