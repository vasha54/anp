from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

class Branch(models.Model):
    _inherit = "res.company"

    is_branch = fields.Boolean(string="Is Branch", default=False)
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        copy=True,
        store=True,
        help="Determine if this branch is active"
    )
    parent_company_id = fields.Many2one(
        'res.company',
        string="Parent Company",
        help="Parent company for consolidation",
        domain=[('is_branch', '=', False)]
    )
    reference = fields.Char(
        string="Reference",
        help="Nearby landmarks or references"
    )
    # Relación con salas
    room_ids = fields.One2many(
        'branch.room',
        'branch_id',
        string='Rooms/Studios',
        help='All rooms and studios in this branch'
    )
    room_count = fields.Integer(
        string='Number of Rooms',
        compute='_compute_room_stats',
        store=False
    )
    schedule_ids = fields.Many2many(
        comodel_name="branch.schedule",
        relation="branch_schedule_res_company_rel",
        column1="branch_id",
        column2="schedule_id",
        string="Work Schedules",
    )
    schedule_rel_ids = fields.One2many(
        'branch.schedule.res.company.rel',
        'branch_id',
        string='Schedule Relations'
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
                    days_overlap = self.env["branch.schedule"]._days_overlap(
                        schedule1.day_of_week_from,
                        schedule1.day_of_week_to,
                        schedule2.day_of_week_from,
                        schedule2.day_of_week_to,
                    )

                    # Verificar solapamiento de horas
                    hours_overlap = self.env["branch.schedule"]._hours_overlap(
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

    @api.depends('room_ids', 'room_ids.capacity')
    def _compute_room_stats(self):
        for branch in self:
            branch.room_count = len(branch.room_ids)

    @api.model
    def create(self, vals):
        records = super().create(vals)
        for company in records:
            if company.is_branch:
                company._link_client_users()
        return records

    def _get_client_group_id(self):
        client_group = self.env.ref('apn_group.group_client', raise_if_not_found=False)
        return client_group.id if client_group else False

    def _link_client_users(self):
        """Agrega esta compañía a la lista de compañías permitidas de todos los usuarios
        que pertenecen a los grupos APN PILATES Client."""
        client_id = self._get_client_group_id()
        group_ids = [gid for gid in [client_id] if gid]
        if not group_ids:
            return
        users = self.env['res.users'].sudo().search([('groups_id', 'in', group_ids)])
        for user in users:
            if self.id not in user.company_ids.ids:
                user.sudo().write({'company_ids': [(4, self.id)]})
