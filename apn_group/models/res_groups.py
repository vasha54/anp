from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

class ResGroups(models.Model):
    _inherit = 'res.groups'

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    is_group_apn = fields.Boolean(
        string="Es grupo de APN Pilates",
        default=False,
    )
    count_users = fields.Integer(
        string="Cantidad de usuarios",
        compute="_compute_users"
    )

    @api.depends("users")
    def _compute_users(self):
        for record in self:
            if record.users:
                record.count_users = len(record.users)
            else:
                record.count_users = 0

    @api.model
    def create(self, vals):
        if 'name' in vals and vals['name']:
            existing = self.search([('name', '=', vals['name'])], limit=1)
            if existing:
                raise ValidationError(_("Ya existe un grupo con el nombre '%s'.") % vals['name'])

        current_context = self.env.context
        if current_context.get('group_apn'):
            vals['is_group_apn'] = True

        return super().create(vals)

    def write(self, vals):
        if 'name' in vals and vals['name']:
            for record in self:
                existing = self.search([('name','=',vals['name']),('id','!=', record.id)], limit=1)
                if existing:
                    raise ValidationError(_("Ya existe otro grupo con el nombre '%s'.") % vals['name'])

        if 'active' in vals:
            for record in self:
                if record.active and vals.get('active') is False:
                    record._deactivate_group()
                if (not record.active) and vals.get('active') is True:
                    record._reactivate_group()

        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.users:
                raise UserError(_("Este rol no puede eliminarse porque está "
                               "asignado a usuarios activos."))
        return super().unlink()


