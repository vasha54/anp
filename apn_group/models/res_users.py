import logging
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResUser(models.Model):
    _inherit = 'res.users'

    is_user_apn = fields.Boolean(string="Es usuario de APN Pilates", default=False)
    confirmed_password = fields.Char(string="Confirmar contraseña", store=False, transient=True)
    apn_group_ids = fields.Many2many(
        'res.groups',
        string='Groups APN Pilates',
        compute='_compute_apn_pilates_groups',
        inverse='_inverse_apn_pilates_groups',
        store=False,
        domain="[('category_id.name', '=', 'APN Pilates')]"
    )
    password_reset_token = fields.Char(string='Token de Reset')
    password_reset_token_expiry = fields.Datetime(string='Expiración del Token')
    password_reset_attempts = fields.Integer(string='Intentos de Reset', default=0)
    last_password_reset_attempt = fields.Datetime(string='Último Intento de Reset')

    @api.depends("groups_id.name")
    def _compute_group_names(self):
        for user in self:
            names = user.groups_id.mapped("name")
            user.group_names = ", ".join(names) if names else ""

    @api.model
    def create(self, vals_list):
        records = vals_list if isinstance(vals_list, list) else [vals_list]
        current_context = self.env.context
        base_group = self.env.ref("base.group_user")
        for vals in records:
            apn_group_ids = vals.get("apn_group_ids", [])
            group_ids_to_set = []

            if apn_group_ids:
                if isinstance(apn_group_ids, list) and apn_group_ids and isinstance(apn_group_ids[0],
                                                                                          (list, tuple)):
                    for command in apn_group_ids:
                        if command[0] == 4:
                            group_ids_to_set.append(command[1])
                        elif command[0] == 6 and len(command) > 2:
                            group_ids_to_set.extend(command[2])
                else:
                    group_ids_to_set = apn_group_ids if isinstance(apn_group_ids, list) else [apn_group_ids]

            # Asegurar grupo base
            if base_group and base_group.id not in group_ids_to_set:
                group_ids_to_set.append(base_group.id)

            # Establecer groups_id y eliminar apn_group_ids y confirmed_password
            vals["groups_id"] = [(6, 0, list(set(group_ids_to_set)))]
            vals.pop("apn_group_ids", None)

            # Validaciones de contraseña
            if vals.get("password") is False or vals.get("confirmed_password") is False:
                raise ValidationError("Campos requeridos faltantes")
            self._validate_password_security(vals["password"])
            if vals["password"] != vals["confirmed_password"]:
                raise ValidationError("Error de confirmación:\n"
                                      "La contraseña y su confirmación deben ser idénticas.\n"
                                      "Verifique que haya escrito la misma contraseña en ambos campos.")

            vals.pop("confirmed_password", None)  # ¡Importante!
            if "user_apn" in current_context:
                vals["is_user_apn"] = True

        return super().create(vals_list)

    def write(self, vals):
        _logger.info("ResUser.write - vals: %s", vals)  # Depuración

        # Validar cambio de contraseña
        if 'password' in vals or 'confirmed_password' in vals:
            if 'password' not in vals or 'confirmed_password' not in vals:
                raise ValidationError(_("Debe proporcionar tanto la contraseña como su confirmación para cambiarla."))
            self._validate_password_security(vals['password'])
            if vals['password'] != vals['confirmed_password']:
                raise ValidationError(_("La contraseña y su confirmación deben coincidir."))
            vals.pop('confirmed_password')

        # No procesar apn_group_ids aquí; el inverso se encargará automáticamente
        return super(ResUser, self).write(vals)

    @api.depends('groups_id')
    def _compute_apn_pilates_groups(self):
        for user in self:
            apn_category = self.env['ir.module.category'].search([('name', '=', 'APN Pilates')], limit=1)
            if apn_category:
                apn_groups = user.groups_id.filtered(lambda g: g.category_id == apn_category)
                user.apn_group_ids = apn_groups
            else:
                user.apn_group_ids = False

    def _inverse_apn_pilates_groups(self):
        _logger.info("Ejecutando _inverse_apn_groups para usuarios: %s", self.ids)
        for user in self:
            _logger.info("Usuario %s: apn_group_ids (nuevo valor) = %s", user.id, user.apn_group_ids.ids)
            apn_category = self.env['ir.module.category'].search([('name', '=', 'APN Pilates')], limit=1)
            if not apn_category:
                _logger.warning("No se encontró la categoría 'APN Pilates', no se pueden asignar grupos APN Pilates.")
                continue

            # Grupos actuales del usuario
            current_groups = user.groups_id
            current_apn = current_groups.filtered(lambda g: g.category_id == apn_category)
            non_apn = current_groups - current_apn
            new_apn = user.apn_group_ids

            # Si no hay cambios, salir
            if set(current_apn.ids) == set(new_apn.ids):
                _logger.info("Usuario %s: grupos APN Pilates sin cambios", user.id)
                continue

            # Asignar la nueva combinación (no APN Pilates + nuevos APN Pilates)
            user.groups_id = non_apn + new_apn
            _logger.info("Usuario %s: groups_id actualizado a: %s", user.id, user.groups_id.ids)

    def _validate_password_security(self, password):
        if len(password) < 8:
            raise ValidationError(_("La contraseña debe tener al menos 8 caracteres."))
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise ValidationError(_("La contraseña debe contener letras y números."))
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_]', password):
            raise ValidationError(_("La contraseña debe contener al menos un carácter especial."))
        return True

