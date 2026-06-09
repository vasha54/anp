from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class BranchSchedule(models.Model):
    _name = "branch.schedule"
    _description = "Branch Work Schedule"
    _order = "day_of_week_from, hour_from"
    _rec_name = "display_name"

    # ─── Relación Many2many con sucursales ─────────────────────
    branch_ids = fields.Many2many(
        comodel_name="res.company",
        relation="apn_branch_schedule_res_company_rel",
        column1="schedule_id",
        column2="branch_id",
        string="Branches",
        domain="[('is_branch', '=', True)]",
    )

    branch_count = fields.Integer(
        string="Branch Count",
        compute="_compute_branch_count",
        store=True,
    )

    # ─── Días ──────────────────────────────────────────────────
    day_of_week_from = fields.Selection(
        selection=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="Start Day",
        required=True,
    )

    day_of_week_to = fields.Selection(
        selection=[
            ("0", "Monday"),
            ("1", "Tuesday"),
            ("2", "Wednesday"),
            ("3", "Thursday"),
            ("4", "Friday"),
            ("5", "Saturday"),
            ("6", "Sunday"),
        ],
        string="End Day",
        required=True,
    )

    # ─── Horas ─────────────────────────────────────────────────
    hour_from = fields.Float(
        string="Start Hour",
        required=True,
        help="Start time (24h format). Example: 22.0 = 22:00, 6.5 = 06:30",
    )

    hour_to = fields.Float(
        string="End Hour",
        required=True,
        help="End time (24h format). If earlier than start hour, "
             "it means the schedule crosses to the next day. "
             "Example: 22:00 to 06:00 = night shift",
    )

    # ─── Indicador de cruce de día ─────────────────────────────
    crosses_midnight = fields.Boolean(
        string="Crosses Midnight",
        compute="_compute_crosses_midnight",
        store=True,
        help="Indicates if the end hour is on the day after the start hour",
    )

    # ─── Campos calculados ─────────────────────────────────────
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )

    day_range = fields.Char(
        string="Day Range",
        compute="_compute_day_range",
        store=True,
    )

    hour_range = fields.Char(
        string="Hour Range",
        compute="_compute_hour_range",
        store=True,
    )

    # ─── Estado ────────────────────────────────────────────────
    active = fields.Boolean(
        string="Active",
        default=True,
    )

    notes = fields.Text(
        string="Notes",
    )

    # ─── Métodos calculados ────────────────────────────────────

    @api.depends("hour_from", "hour_to")
    def _compute_crosses_midnight(self):
        for record in self:
            if record.hour_from is not False and record.hour_to is not False:
                # Si hour_to es menor o igual que hour_from,
                # significa que cruza la medianoche
                record.crosses_midnight = record.hour_to <= record.hour_from
            else:
                record.crosses_midnight = False

    @api.depends("branch_ids")
    def _compute_branch_count(self):
        for record in self:
            record.branch_count = len(record.branch_ids)

    @api.depends("day_of_week_from", "day_of_week_to",
                 "hour_from", "hour_to")
    def _compute_display_name(self):
        for record in self:
            if record.day_of_week_from and record.hour_from:
                record.display_name = _(
                    "%(days)s | %(hours)s"
                ) % {
                                          "days": record.day_range or "",
                                          "hours": record.hour_range or "",
                                      }
            else:
                record.display_name = _("New Schedule")

    @api.depends("day_of_week_from", "day_of_week_to")
    def _compute_day_range(self):
        day_labels = dict(self._fields["day_of_week_from"].selection)
        for record in self:
            from_label = day_labels.get(record.day_of_week_from, "")
            to_label = day_labels.get(record.day_of_week_to, "")
            if record.day_of_week_from == record.day_of_week_to:
                record.day_range = from_label
            else:
                record.day_range = f"{from_label} - {to_label}"

    @api.depends("hour_from", "hour_to")
    def _compute_hour_range(self):
        for record in self:
            if record.hour_from is not False and record.hour_to is not False:
                from_str = self._float_to_time_str(record.hour_from)
                to_str = self._float_to_time_str(record.hour_to)
                if record.crosses_midnight:
                    record.hour_range = _(
                        "%(from)s - %(to)s (next day)"
                    ) % {"from": from_str, "to": to_str}
                else:
                    record.hour_range = _(
                        "%(from)s - %(to)s"
                    ) % {"from": from_str, "to": to_str}
            else:
                record.hour_range = ""

    # ─── Protección contra modificación/eliminación ────────────

    def _check_schedule_in_use(self):
        """Verifica si el horario está asociado a alguna sucursal"""
        self.ensure_one()
        if self.branch_ids:
            raise UserError(_(
                "You cannot modify or delete this schedule because it is "
                "associated with the following branches:\n%(branches)s\n\n"
                "Remove the schedule from all branches before proceeding."
            ) % {
                                "branches": "\n".join(
                                    f"• {branch.name}" for branch in self.branch_ids
                                )
                            })

    def write(self, vals):
        # Proteger horarios en uso contra modificación
        protected_fields = set(vals.keys()) - {"active", "notes", "branch_ids"}
        if protected_fields:
            for record in self:
                record._check_schedule_in_use()

        result = super().write(vals)

        # Validar solapamientos si se modificaron branch_ids
        if "branch_ids" in vals:
            for record in self:
                record._validate_no_overlap_for_branches()

        return result

    def unlink(self):
        # Proteger horarios en uso contra eliminación
        for record in self:
            record._check_schedule_in_use()
        return super().unlink()

    # ─── Validaciones ──────────────────────────────────────────

    @api.constrains("day_of_week_from", "day_of_week_to")
    def _check_days_order(self):
        for record in self:
            if record.day_of_week_from and record.day_of_week_to:
                if int(record.day_of_week_from) > int(record.day_of_week_to):
                    raise ValidationError(_(
                        "The start day must be earlier than or equal to "
                        "the end day."
                    ))

    @api.constrains("hour_from", "hour_to", "day_of_week_from", "day_of_week_to")
    def _check_hours(self):
        for record in self:
            if record.hour_from is not False and record.hour_to is not False:
                if record.hour_from < 0 or record.hour_from >= 24:
                    raise ValidationError(_(
                        "Start hour must be between 00:00 and 23:59."
                    ))
                if record.hour_to < 0 or record.hour_to >= 24:
                    raise ValidationError(_(
                        "End hour must be between 00:00 and 23:59."
                    ))
            if record.day_of_week_from and record.day_of_week_to:
                if record.day_of_week_from == record.day_of_week_to:
                    if record.hour_from == record.hour_to:
                        raise ValidationError(_(
                            "Start hour and end hour cannot be the same."
                        ))
                    if record.hour_from > record.hour_to:
                        raise ValidationError(_("The start hour cannot be later than the end hour."))

    @api.constrains("branch_ids", "day_of_week_from", "day_of_week_to",
                    "hour_from", "hour_to", "active")
    def _check_no_overlap_in_branches(self):
        """Valida que no haya solapamiento de horarios en las sucursales"""
        for record in self:
            if record.active:
                record._validate_no_overlap_for_branches()

    # ─── Método de validación de solapamiento mejorado ─────────

    def _validate_no_overlap_for_branches(self):
        """
        Verifica que este horario no se solape con otros horarios
        activos en las mismas sucursales.
        Soporta horarios que cruzan días (ej: 22:00 - 06:00)
        """
        self.ensure_one()

        if not self.active or not self.branch_ids:
            return

        # Obtener todos los horarios activos de las sucursales
        # asignadas, excluyendo el horario actual
        overlapping_schedules = self.search([
            ("id", "!=", self.id),
            ("branch_ids", "in", self.branch_ids.ids),
            ("active", "=", True),
        ])

        conflicts = []

        for other in overlapping_schedules:
            # Verificar si comparten sucursales
            common_branches = self.branch_ids & other.branch_ids
            if not common_branches:
                continue

            # Verificar solapamiento con soporte para cruce de días
            if self._schedules_overlap(self, other):
                conflict_branches = common_branches.mapped("name")
                conflicts.append({
                    "schedule": other,
                    "branches": conflict_branches,
                })

        if conflicts:
            error_msg = _(
                "This schedule overlaps with existing schedules "
                "in the following branches:\n\n"
            )
            for conflict in conflicts:
                error_msg += _("• Schedule '%(schedule)s' in: %(branches)s\n") % {
                    "schedule": conflict["schedule"].display_name,
                    "branches": ", ".join(conflict["branches"]),
                }

            raise ValidationError(error_msg)

    # ─── Métodos helper ─────────────────────────────────────────

    @api.model
    def _float_to_time_str(self, float_hour):
        """Convierte hora flotante a string HH:MM"""
        hours = int(float_hour)
        minutes = int(round((float_hour - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    @api.model
    def _schedules_overlap(self, schedule1, schedule2):
        """
        Determina si dos horarios se solapan, soportando horarios
        que cruzan días (ej: 22:00 - 06:00).

        Estrategia: Convertir cada horario a intervalos lineales en
        una "semana extendida" (0h Monday = 0, Sunday 24h = 168).
        """
        # Convertir cada día a su hora de inicio en la semana (0 = Lunes 00:00)
        day_to_hours = {
            "0": 0,  # Monday
            "1": 24,  # Tuesday
            "2": 48,  # Wednesday
            "3": 72,  # Thursday
            "4": 96,  # Friday
            "5": 120,  # Saturday
            "6": 144,  # Sunday
        }

        def get_intervals(schedule):
            """Obtiene todos los intervalos de un horario en la semana"""
            intervals = []
            start_day = int(schedule.day_of_week_from)
            end_day = int(schedule.day_of_week_to)

            for day in range(start_day, end_day + 1):
                day_start = day_to_hours[str(day)]

                if schedule.crosses_midnight:
                    # El horario cubre desde hour_from del día actual
                    # hasta hour_to del día siguiente
                    intervals.append((
                        day_start + schedule.hour_from,
                        day_start + 24 + schedule.hour_to
                    ))
                else:
                    # Horario normal dentro del mismo día
                    intervals.append((
                        day_start + schedule.hour_from,
                        day_start + schedule.hour_to
                    ))

            return intervals

        intervals1 = get_intervals(schedule1)
        intervals2 = get_intervals(schedule2)

        # Verificar si algún par de intervalos se solapan
        for start1, end1 in intervals1:
            for start2, end2 in intervals2:
                # Solapamiento: max(start1, start2) < min(end1, end2)
                if max(start1, start2) < min(end1, end2):
                    return True

        return False

    @api.model
    def _days_overlap(self, from1, to1, from2, to2):
        """
        Verifica si dos rangos de días se solapan.
        Mantenido por compatibilidad y para uso desde res.company.
        """
        f1, t1, f2, t2 = map(int, [from1, to1, from2, to2])
        return max(f1, f2) <= min(t1, t2)

    @api.model
    def _hours_overlap(self, hfrom1, hto1, hfrom2, hto2):
        """
        Verifica si dos rangos de horas se solapan.
        Soporta horarios que cruzan medianoche.
        Mantenido por compatibilidad y para uso desde res.company.
        """

        def normalize_interval(start, end):
            """Convierte un intervalo a formato lineal"""
            if end <= start:
                # Cruza medianoche: 22:00 - 06:00 → [22, 30]
                return (start, end + 24)
            return (start, end)

        nstart1, nend1 = normalize_interval(hfrom1, hto1)
        nstart2, nend2 = normalize_interval(hfrom2, hto2)

        return max(nstart1, nstart2) < min(nend1, nend2)

    # ─── Acciones ──────────────────────────────────────────────

    def name_get(self):
        result = []
        for record in self:
            name = record.display_name or _("New Schedule")
            if record.branch_count:
                name += _(" (%(count)d branches)") % {
                    "count": record.branch_count
                }
            result.append((record.id, name))
        return result

    def action_view_branches(self):
        """Abrir lista de sucursales que usan este horario"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Branches using this schedule"),
            "res_model": "res.company",
            "view_mode": "list,form",
            "domain": [("id", "in", self.branch_ids.ids)],
            "context": {"default_is_branch": True},
        }

    @api.depends("day_of_week_from", "day_of_week_to",
                 "hour_from", "hour_to")
    def _compute_display_name(self):
        day_labels = dict(self._fields["day_of_week_from"].selection)
        for record in self:
            if record.day_of_week_from and record.hour_from is not False:
                from_day = day_labels.get(record.day_of_week_from, "")
                to_day = day_labels.get(record.day_of_week_to, "")
                from_hour = self._float_to_time_str(record.hour_from)
                to_hour = self._float_to_time_str(record.hour_to)

                # La cadena base debe ser traducible con marcadores %s
                record.display_name = _(
                    "From %(from_day)s to %(to_day)s (%(from_hour)s - %(to_hour)s)"
                ) % {
                                          "from_day": from_day,
                                          "to_day": to_day,
                                          "from_hour": from_hour,
                                          "to_hour": to_hour,
                                      }
            else:
                record.display_name = _("New Schedule")