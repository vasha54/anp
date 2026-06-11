from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BranchRoom(models.Model):
    _name = 'branch.room'
    _description = 'Branch Room/Studio'
    _order = 'branch_id, name'
    _rec_name = 'complete_name'

    branch_id = fields.Many2one(
        'res.company',
        string='Branch',
        required=True,
        ondelete='cascade',
        domain=[('is_branch', '=', True)],
        help='Branch to which this room belongs'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='branch_id.parent_company_id',
        store=True,
        readonly=True
    )

    name = fields.Char(
        string='Room Name',
        required=True,
        help='Example: Main Studio, Private Room 1, Reformer Room, etc.'
    )

    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        store=True
    )

    capacity = fields.Integer(
        string='Capacity (people)',
        required=True,
        default=10,
        help='Maximum number of people allowed in the room'
    )

    _sql_constraints = [
        ('unique_room_per_branch',
         'UNIQUE(branch_id, name)',
         'A room with this name already exists in this branch. Please use a different name.'),
        ('check_capacity_positive',
         'CHECK(capacity > 0)',
         'Capacity must be greater than 0.')
    ]

    @api.depends('branch_id.name', 'name')
    def _compute_complete_name(self):
        for room in self:
            if room.branch_id and room.name:
                room.complete_name = f"{room.branch_id.name} - {room.name}"
            else:
                room.complete_name = room.name or ''

    def _check_duplicate_name(self):
        """Método centralizado para validar duplicados"""
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(_("The room name cannot be empty."))

            existing = self.search([
                ('branch_id', '=', record.branch_id.id),
                ('name', 'ilike', record.name.strip()),
                ('id', '!=', record.id)
            ])

            if existing:
                raise ValidationError(_(
                    "A room named '%(room_name)s' already exists in branch '%(branch_name)s'. "
                    "Please use a unique name for each room.",
                    room_name=record.name,
                    branch_name=record.branch_id.name
                ))

    @api.model_create_multi
    def create(self, vals_list):
        """Crear registros con validación de duplicados"""
        # Crear los registros primero
        records = super().create(vals_list)
        # Luego validar
        records._check_duplicate_name()
        return records

    def write(self, vals):
        """Modificar registros con validación de duplicados"""
        result = super().write(vals)
        # Validar después de escribir si cambió nombre o sucursal
        if 'name' in vals or 'branch_id' in vals:
            self._check_duplicate_name()
        return result

    @api.constrains('branch_id', 'name')
    def _check_unique_room_per_branch(self):
        """Validación adicional por restricción (respaldo)"""
        self._check_duplicate_name()