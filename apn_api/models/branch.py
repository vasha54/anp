from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

class Branch(models.Model):
    _inherit = "res.company"

    state = fields.Json(
        string="State in JSON",
        compute="_compute_state_data",
        store=False,
    )
    country = fields.Json(
        string="Country in JSON",
        compute="_compute_country_data",
        store=False,
    )
    parent_company = fields.Json(
        string="Parent Company in JSON",
        compute="_compute_parent_company_data",
        store=False,
    )
    rooms = fields.Json(
        string="Rooms in JSON",
        compute="_compute_room_data",
        store=False,
    )
    schedules = fields.Json(
        string="Schedules in JSON",
        compute="_compute_schedule_data",
        store=False,
    )

    def _compute_state_data(self):
        for record in self:
            record.state = record.state_id.read(
                [
                    "id",
                    "name",
                ]
            )[0]

    def _compute_country_data(self):
        for record in self:
            record.country = record.country_id.read(
                [
                    "id",
                    "name",
                ]
            )[0]

    def _compute_parent_company_data(self):
        for record in self:
            record.parent_company = record.parent_company_id.read(
                [
                    "id",
                    "name",
                ]
            )[0]

    def _compute_room_data(self):
        for record in self:
            record.rooms = record.room_ids.read(
                [
                    "id",
                    "name",
                    "capacity",
                ]
            )

    def _compute_schedule_data(self):
        for record in self:
            schedules_data = []
            for schedule in record.schedule_ids:
                data = {
                    'id': schedule.id,
                    'day_of_week_from': schedule.day_of_week_from,
                    'day_of_week_from_label': dict(schedule._fields['day_of_week_from'].selection).get(
                        schedule.day_of_week_from),
                    'day_of_week_to': schedule.day_of_week_to,
                    'day_of_week_to_label': dict(schedule._fields['day_of_week_to'].selection).get(
                        schedule.day_of_week_to),
                    'hour_from': schedule.hour_from,
                    'hour_to': schedule.hour_to,
                }
                schedules_data.append(data)
            record.schedules = schedules_data

    @api.model
    def get_branches_locations(self, page=1, limit=20):
        """
        Retorna listado de sucursales con geolocalización con paginación
        """
        page = int(page) if page else 1
        limit = int(limit) if limit else 20
        offset = (page - 1) * limit

        domain = [
            ("is_branch", "=", True),
            ("latitude", "!=", False),
            ("longitude", "!=", False),
        ]

        total = self.search_count(domain)
        branches = self.search(domain, offset=offset, limit=limit)

        data = [
            {
                "id": b.id,
                "name": b.name,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "street": b.street,
                "zip": b.zip,
                "city": b.city,
                "state": b.state_id.name,
                "country": b.country_id.name,
            }
            for b in branches
        ]

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total // limit) + (1 if total % limit else 0),
            "branches": data,
        }

    @api.model
    def _calculate_distance_meters(self, lat1, lon1, lat2, lon2):
        """
        Calcula la distancia en metros entre dos puntos geográficos
        usando la fórmula del haversine.
        """
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000.0  # Radio de la Tierra en metros

        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    @api.model
    def get_nearby_branches(self, latitude, longitude, max_distance=None):
        """
        Retorna sucursales cercanas a una coordenada dada.
        Si no se proporciona max_distance, se usa el valor configurado en
        el parámetro del sistema.
        """
        # Si no se recibe max_distance, tomamos el valor por defecto del sistema
        if max_distance is None:
            max_distance = float(
                self.env["ir.config_parameter"].sudo().get_param(
                    "apn_company.nearby_branches_default_distance_meters", 350
                )
            )
        else:
            max_distance = float(max_distance)

        branches = self.search([
            ("is_branch", "=", True),
            ("latitude", "!=", False),
            ("longitude", "!=", False),
            ("active","=", True),
        ])

        nearby = []
        for branch in branches:
            distance = self._calculate_distance_meters(
                latitude,
                longitude,
                branch.latitude,
                branch.longitude,
            )
            if distance <= max_distance:
                nearby.append({
                    "id": branch.id,
                    "name": branch.name,
                    "latitude": branch.latitude,
                    "longitude": branch.longitude,
                    "distance_meters": round(distance, 2),
                    "street": branch.street,
                    "zip": branch.zip,
                    "city": branch.city,
                    "state": branch.state_id.name,
                    "country": branch.country_id.name,
                })

        nearby = sorted(nearby, key=lambda b: b["distance_meters"])
        return nearby