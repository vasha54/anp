from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    product_tags = fields.Json(
        string="Product Tags JSON",
        compute="_compute_product_tags",
        store=False,
    )
    taxes = fields.Json(
        string="Taxes JSON",
        compute="_compute_product_taxes",
        store=False,
    )
    categ = fields.Json(
        string="Category JSON",
        compute="_compute_product_categ",
        store=False,
    )
    companies = fields.Json(
        string="Company JSON",
        compute="_compute_product_companies",
        store=False,
    )
    attribute_lines = fields.Json(
        string="Attribute Lines JSON",
        compute="_compute_product_attribute_lines",
        store=False,
    )
    variant_values = fields.Json(
        string="Variant Attribute Values JSON",
        compute="_compute_product_variant_values",
        store=False,
    )
    product_tmpl = fields.Json(
        string="Product Template JSON",
        compute="_compute_product_product_tmpl",
        store=False,
    )

    def _compute_product_tags(self):
        for record in self:
            if record.product_tag_ids:
                record.product_tags = record.product_tag_ids.read(
                    ["id", "name", "color"]
                )
            else:
                record.product_tags = None

    def _compute_product_taxes(self):
        for record in self:
            if record.taxes_id:
                record.taxes = record.taxes_id.read(
                    ['id', 'name', 'amount', 'type_tax_use', 'description', 'amount_type', 'price_include']
                )
            else:
                record.taxes = None

    def _compute_product_categ(self):
        for record in self:
            if record.categ_id:
                record.categ = record.categ_id.read(['id', 'name'])[0]
            else:
                record.categ = None

    def _compute_product_companies(self):
        for record in self:
            if record.company_ids:
                record.companies = record.company_ids.read(['id', 'name'])
            else:
                record.companies = None

    def _compute_product_attribute_lines(self):
        for record in self:
            if record.attribute_line_ids:
                lines = []
                for line in record.attribute_line_ids:
                    value_data = line.value_ids.read([
                        'id', 'name', 'color', 'sequence'
                    ])
                    lines.append({
                        'id': line.id,
                        'sequence': line.sequence,
                        'attribute_id': line.attribute_id.id,
                        'attribute_name': line.attribute_id.name,
                        'value_count': line.value_count,
                        'value_ids': value_data,
                    })
                record.attribute_lines = lines
            else:
                record.attribute_lines = None

    def _compute_product_variant_values(self):
        for record in self:
            if record.product_template_variant_value_ids:
                values = []
                for ptav in record.product_template_variant_value_ids:
                    # ptav es product.template.attribute.value
                    attr_value = ptav.product_attribute_value_id  # el valor real
                    values.append({
                        'id': ptav.id,
                        'attribute_id': ptav.attribute_id.id,
                        'attribute_name': ptav.attribute_id.name,
                        'value_id': attr_value.id,
                        'value_name': attr_value.name,
                        'value_color': attr_value.color,
                        'price_extra': ptav.price_extra,
                    })
                record.variant_values = values
            else:
                record.variant_values = None

    def _compute_product_product_tmpl(self):
        for record in self:
            if record.product_tmpl_id:
                record.product_tmpl = record.product_tmpl_id.read([
                    'id',
                    'name',
                ])[0]
            else:
                record.product_tmpl = None

