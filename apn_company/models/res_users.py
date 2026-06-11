from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api


class ResUsersCompany(models.Model):
    _inherit = "res.users"

    # Compañías donde es administrador
    admin_company_ids = fields.Many2many(
        'res.company',
        'res_users_admin_company_rel',
        'user_id',
        'company_id',
        string="Administered Companies",
        domain="[('id', 'in', company_ids), ('is_branch', '=', False)]",
        help="Companies where this user is an administrator"
    )

    # Sucursales donde es administrador
    admin_branch_ids = fields.Many2many(
        'res.company',
        'res_users_admin_branch_rel',
        'user_id',
        'company_id',
        string="Administered Branches",
        domain="[('id', 'in', company_ids), ('is_branch', '=', True)]",
        help="Branches where this user is an administrator"
    )

    # Sucursales donde es operador
    operator_branch_ids = fields.Many2many(
        'res.company',
        'res_users_operator_branch_rel',
        'user_id',
        'company_id',
        string="Operated Branches",
        domain="[('id', 'in', company_ids), ('is_branch', '=', True)]",
        help="Branches where this user is an operator"
    )

    # Sucursales donde es instructor
    instructor_branch_ids = fields.Many2many(
        'res.company',
        'res_users_instructor_branch_rel',
        'user_id',
        'company_id',
        string="Instructor Branches",
        domain="[('id', 'in', company_ids), ('is_branch', '=', True)]",
        help="Branches where this user is an instructor"
    )

    def _get_assigned_companies(self):
        """Obtiene todas las compañías asignadas en cualquier rol"""
        self.ensure_one()
        assigned = set()

        if self.admin_company_ids:
            assigned.update(self.admin_company_ids.ids)

        if self.admin_branch_ids:
            assigned.update(self.admin_branch_ids.ids)
            # Agregar también las compañías padre de las sucursales
            for branch in self.admin_branch_ids:
                if branch.parent_company_id:
                    assigned.add(branch.parent_company_id.id)

        if self.operator_branch_ids:
            assigned.update(self.operator_branch_ids.ids)

        if self.instructor_branch_ids:
            assigned.update(self.instructor_branch_ids.ids)

        return assigned

    @api.onchange('company_ids')
    def _onchange_company_ids(self):
        """Clear role assignments when companies/branches are removed"""
        for record in self:
            # Obtener IDs de compañías actuales
            current_company_ids = record.company_ids.ids

            # Limpiar asignaciones que ya no están en company_ids
            record.admin_company_ids = record.admin_company_ids.filtered(
                lambda c: c.id in current_company_ids
            )
            record.admin_branch_ids = record.admin_branch_ids.filtered(
                lambda c: c.id in current_company_ids
            )
            record.operator_branch_ids = record.operator_branch_ids.filtered(
                lambda c: c.id in current_company_ids
            )
            record.instructor_branch_ids = record.instructor_branch_ids.filtered(
                lambda c: c.id in current_company_ids
            )

    def _get_assigned_companies(self):
        """Obtener conjunto de IDs de compañías con roles asignados"""
        assigned = set()
        assigned.update(self.admin_company_ids.ids)
        assigned.update(self.admin_branch_ids.ids)
        assigned.update(self.operator_branch_ids.ids)
        assigned.update(self.instructor_branch_ids.ids)
        return assigned

    @api.onchange('company_ids', 'admin_company_ids', 'admin_branch_ids',
                  'operator_branch_ids', 'instructor_branch_ids')
    def _onchange_check_roles(self):
        """Mostrar advertencia visual antes de guardar"""
        if self.id and self.company_ids:
            assigned = self._get_assigned_companies()
            company_set = set(self.company_ids.ids)
            unassigned = company_set - assigned

            if unassigned:
                return {
                    'warning': {
                        'title': _('Missing Role Assignment'),
                        'message': _(
                            '%(count)d companies/branches have no role assigned. '
                            'Please assign them to at least one role before saving.'
                        ) % {'count': len(unassigned)},
                    }
                }

    def _is_exempt_from_role_validation(self):
        """Verifica si el usuario está exento de la validación de roles"""
        self.ensure_one()

        # Excluir SUPERUSER_ID
        if self.id == SUPERUSER_ID:
            return True

        # Excluir OdooBot
        odoobot = self.env.ref('base.user_root', raise_if_not_found=False)
        if odoobot and self.id == odoobot.id:
            return True

        # Excluir grupos específicos
        return (
                self.has_group('apn_group.group_client') or
                self.has_group('apn_group.group_admin_apn_pilates') or
                self.has_group('apn_group.group_support_anp_pilates')
        )

    @api.constrains('company_ids', 'admin_company_ids', 'admin_branch_ids',
                    'operator_branch_ids', 'instructor_branch_ids')
    def _check_companies_have_role(self):
        """Validación final: todas las compañías deben tener al menos un rol"""
        for user in self:
            # Si el usuario pertenece a grupos exentos, saltar validación
            _logger.info(f"{user.name} {user._is_exempt_from_role_validation()}")
            if user._is_exempt_from_role_validation():
                continue

            assigned = user._get_assigned_companies()
            company_set = set(user.company_ids.ids)
            unassigned = company_set - assigned

            if unassigned:
                unassigned_companies = self.env['res.company'].browse(list(unassigned))
                names = ', '.join(unassigned_companies.mapped('name'))
                raise ValidationError(
                    _('These companies/branches must be assigned to at least one role:\n%s') % names
                )

    # # Campo computado: todas las sucursales asignadas (admin + operador + instructor)
    # all_branch_ids = fields.Many2many(
    #     'res.company',
    #     'res_users_all_branch_rel',
    #     'user_id',
    #     'company_id',
    #     string="All Branches",
    #     compute='_compute_all_branches',
    #     store=True
    # )

    # # Campos booleanos para controlar visibilidad en vistas
    # is_admin_company = fields.Boolean(
    #     string="Is Company Admin",
    #     compute='_compute_apn_roles',
    # )
    #
    # is_admin_branch = fields.Boolean(
    #     string="Is Branch Admin",
    #     compute='_compute_apn_roles',
    # )
    #
    # is_operator_branch = fields.Boolean(
    #     string="Is Branch Operator",
    #     compute='_compute_apn_roles',
    # )
    #
    # is_instructor = fields.Boolean(
    #     string="Is Instructor",
    #     compute='_compute_apn_roles',
    # )
    #
    # is_client = fields.Boolean(
    #     string="Is Client",
    #     compute='_compute_apn_roles',
    # )
    #
    # has_apn_access = fields.Boolean(
    #     string="Has APN Access",
    #     compute='_compute_apn_roles',
    # )
    #
    # @api.depends('apn_group_ids')
    # def _compute_apn_roles(self):
    #     """Calcula los roles APN basados en los grupos del usuario"""
    #     for user in self:
    #         user.is_admin_company = user.has_group('apn_group.group_admin_company')
    #         user.is_admin_branch = user.has_group('apn_group.group_admin_branch')
    #         user.is_operator_branch = user.has_group('apn_group.group_operator_branch')
    #         user.is_instructor = user.has_group('apn_group.group_instructor')
    #         user.is_client = user.has_group('apn_group.group_client')
    #         user.has_apn_access = (
    #                 user.is_admin_company or
    #                 user.is_admin_branch or
    #                 user.is_operator_branch or
    #                 user.is_instructor or
    #                 user.is_client
    #         )
    #
    # @api.depends('admin_branch_ids', 'operator_branch_ids', 'instructor_branch_ids')
    # def _compute_all_branches(self):
    #     """Combina todas las sucursales asignadas por cualquier rol"""
    #     for user in self:
    #         user.all_branch_ids = (
    #                 user.admin_branch_ids |
    #                 user.operator_branch_ids |
    #                 user.instructor_branch_ids
    #         )
    #
    # @api.model
    # def get_user_session_data(self):
    #     """Sobreescribir para incluir las compañías personalizadas"""
    #     user = self.env.user
    #
    #     # Obtener compañías según tu lógica de negocio
    #     if user._is_admin():
    #         # Admin ve todas las compañías
    #         companies = self.env['res.company'].sudo().search([])
    #     else:
    #         # Usuario normal ve sus compañías asignadas
    #         companies = user.get_user_accessible_companies()
    #
    #     user_companies = companies.read(['id', 'name', 'sequence'])
    #
    #     # Asegurar que la compañía principal esté en la lista
    #     if user.company_id and user.company_id.id not in companies.ids:
    #         main_company = user.company_id.read(['id', 'name'])[0]
    #         user_companies.insert(0, main_company)
    #
    #     _logger.info("PASE POR AQUI CON EL GAUCHO POWER")
    #
    #     return {
    #         'uid': user.id,
    #         'name': user.name,
    #         'email': user.email or user.login,
    #         'company_id': user.company_id.id,
    #         'user_companies': user_companies,
    #         # Datos adicionales que puedas necesitar
    #         'is_apn_admin': user._is_admin(),
    #         'user_branches': user.all_branch_ids.read(['id', 'name']),
    #     }
    #
    # def _ensure_company_ids(self):
    #     """Asegura que company_ids esté sincronizado con tu lógica"""
    #     for user in self:
    #         accessible_companies = user.get_user_accessible_companies()
    #         if set(user.company_ids.ids) != set(accessible_companies.ids):
    #             user.company_ids = [(6, 0, accessible_companies.ids)]
    #
    # @api.onchange('admin_company_ids')
    # def _onchange_admin_company_ids(self):
    #     """Al seleccionar compañías administradas, actualizar sucursales administradas"""
    #     if self.admin_company_ids:
    #         # Obtener todas las sucursales de las compañías seleccionadas
    #         branches = self.env['res.company'].search([
    #             ('is_branch', '=', True),
    #             ('parent_company_id', 'in', self.admin_company_ids.ids)
    #         ])
    #         return {
    #             'domain': {
    #                 'admin_branch_ids': [
    #                     ('id', 'in', branches.ids),
    #                     ('is_branch', '=', True)
    #                 ]
    #             }
    #         }
    #
    # def get_user_accessible_companies(self):
    #     """Retorna todas las compañías accesibles para el usuario"""
    #     self.ensure_one()
    #
    #     # Si es administrador APN o soporte técnico, ver todas
    #     if self._is_admin():
    #         return self.env['res.company'].search([])
    #
    #     # Combinar todas las compañías asignadas
    #     companies = self.env['res.company']
    #
    #     # Siempre incluir la compañía principal
    #     if self.company_id:
    #         companies |= self.company_id
    #
    #     # Agregar compañías asignadas explícitamente
    #     if self.company_ids:
    #         companies |= self.company_ids
    #
    #     if self.admin_company_ids:
    #         companies |= self.admin_company_ids
    #
    #     # Agregar compañías padre de las sucursales
    #     branches = self.all_branch_ids
    #     if branches:
    #         parent_companies = branches.mapped('parent_company_id')
    #         companies |= parent_companies
    #
    #     # Si aún no hay compañías, usar la compañía actual del entorno
    #     if not companies:
    #         companies = self.env.company
    #
    #     return companies
    #
    # def get_user_branches_by_role(self, role):
    #     """Obtiene las sucursales del usuario por rol específico"""
    #     self.ensure_one()
    #
    #     role_mapping = {
    #         'admin': self.admin_branch_ids,
    #         'operator': self.operator_branch_ids,
    #         'instructor': self.instructor_branch_ids,
    #         'all': self.all_branch_ids,
    #     }
    #
    #     return role_mapping.get(role, self.env['res.company'])
    #
    # def _is_admin(self):
    #     """Verifica si el usuario es administrador del sistema APN"""
    #     is_admin = False
    #     groups_list = [
    #         'apn_group.group_admin_apn_pilates',
    #         'apn_group.group_support_anp_pilates',
    #         'base.group_erp_manager',
    #         'base.group_system',
    #     ]
    #     for g in groups_list:
    #         is_admin = is_admin or self.has_group(g)
    #     return is_admin
    #
    # def _has_apn_access(self):
    #     """Verifica si el usuario tiene algún rol en APN"""
    #     return self.has_group('apn_group.group_admin_apn_pilates') or \
    #         self.has_group('apn_group.group_support_anp_pilates') or \
    #         self.has_group('apn_group.group_admin_company') or \
    #         self.has_group('apn_group.group_admin_branch') or \
    #         self.has_group('apn_group.group_operator_branch') or \
    #         self.has_group('apn_group.group_instructor')
    #
    # def _is_company_admin(self):
    #     """Verifica si el usuario es administrador de alguna compañía"""
    #     return self.has_group('apn_group.group_admin_company') and \
    #         bool(self.admin_company_ids)
    #
    # def _is_branch_admin(self):
    #     """Verifica si el usuario es administrador de alguna sucursal"""
    #     return self.has_group('apn_group.group_admin_branch') and \
    #         bool(self.admin_branch_ids)
    #
    # def _is_branch_operator(self):
    #     """Verifica si el usuario es operador de alguna sucursal"""
    #     return self.has_group('apn_group.group_operator_branch') and \
    #         bool(self.operator_branch_ids)
    #
    # def _is_instructor(self):
    #     """Verifica si el usuario es instructor de alguna sucursal"""
    #     return self.has_group('apn_group.group_instructor') and \
    #         bool(self.instructor_branch_ids)
    #
    # def get_user_branches(self):
    #     """
    #     Retorna todas las sucursales donde el usuario tiene algún rol.
    #     Útil para filtrar datos en vistas y reportes.
    #     """
    #     self.ensure_one()
    #
    #     if self._is_admin():
    #         return self.env['res.company'].search([('is_branch', '=', True)])
    #
    #     return self.all_branch_ids
    #
    # def get_user_role_in_branch(self, branch_id):
    #     """
    #     Retorna el rol del usuario en una sucursal específica.
    #     Útil para permisos granulares.
    #     """
    #     self.ensure_one()
    #
    #     roles = []
    #     if branch_id in self.admin_branch_ids.ids:
    #         roles.append('admin')
    #     if branch_id in self.operator_branch_ids.ids:
    #         roles.append('operator')
    #     if branch_id in self.instructor_branch_ids.ids:
    #         roles.append('instructor')
    #
    #     return roles
    #
    # @api.constrains('company_ids', 'company_id')
    # def _check_company_ids(self):
    #     """Asegura que el usuario tenga al menos una compañía"""
    #     for user in self:
    #         if not user.company_id:
    #             raise ValidationError(
    #                 "User must have a main company assigned."
    #             )
    #
    #
    # @api.onchange('groups_id')
    # def _onchange_groups_id(self):
    #     """Al cambiar grupos, asegurar que tenga compañías asignadas"""
    #     # Si se agrega un grupo APN, asegurar que tenga al menos una compañía
    #     if self._has_apn_access():
    #         if not self.company_id:
    #             self.company_id = self.env.company.id
    #         if not self.company_ids:
    #             self.company_ids = [(4, self.company_id.id)]
    #
    # def _inverse_apn_pilates_groups(self):
    #     """
    #     Extiende el inverse original para agregar limpieza de campos
    #     cuando se quitan roles
    #     """
    #     # Guardar estado anterior
    #     old_roles = {
    #         user.id: {
    #             'is_admin_company': user.is_admin_company,
    #             'is_admin_branch': user.is_admin_branch,
    #             'is_operator_branch': user.is_operator_branch,
    #             'is_instructor': user.is_instructor,
    #         }
    #         for user in self
    #     }
    #
    #     # Llamar al método original (super)
    #     result = super(ResUsersCompany, self)._inverse_apn_pilates_groups()
    #
    #     # Limpiar campos según cambios de rol
    #     for user in self:
    #         user._compute_apn_roles()
    #         old = old_roles.get(user.id, {})
    #         vals_to_clear = {}
    #
    #         if old.get('is_admin_company') and not user.is_admin_company and user.admin_company_ids:
    #             vals_to_clear['admin_company_ids'] = [(5, 0, 0)]
    #
    #         if old.get('is_admin_branch') and not user.is_admin_branch and user.admin_branch_ids:
    #             vals_to_clear['admin_branch_ids'] = [(5, 0, 0)]
    #
    #         if old.get('is_operator_branch') and not user.is_operator_branch and user.operator_branch_ids:
    #             vals_to_clear['operator_branch_ids'] = [(5, 0, 0)]
    #
    #         if old.get('is_instructor') and not user.is_instructor and user.instructor_branch_ids:
    #             vals_to_clear['instructor_branch_ids'] = [(5, 0, 0)]
    #
    #         if vals_to_clear:
    #             user.sudo().write(vals_to_clear)
    #             _logger.info("Usuario %s: Campos limpiados: %s", user.id, list(vals_to_clear.keys()))
    #
    #     return result

