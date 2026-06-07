from odoo import api, fields, models
from odoo.exceptions import ValidationError

class DataBarChart(models.Model):
    _name = "data.bar.chart"


class DataBubbleChart(models.Model):
    _name = "data.bubble.chart"


class DataDonutChart(models.Model):
    _name = "data.donut.chart"

    label = fields.Char("Label")
    value = fields.Float("Value")

class DataLineChart(models.Model):
    _name = "data.line.chart"

class DataPieChart(models.Model):
    _name = "data.pie.chart"

class DataPolarAreaChart(models.Model):
    _name = "data.polar.area.chart"

class DataRadalChart(models.Model):
    _name = "data.radal.chart"

class DataScatterChart(models.Model):
    _name = "data.scatter.chart"