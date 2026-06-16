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