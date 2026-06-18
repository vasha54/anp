import logging
import traceback
from odoo import models, fields, api
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    # Campos para guardar las preferencias de filtro
    filter_period = fields.Selection([
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('last_quarter', 'Last Quarter'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
        ('custom', 'Custom'),
    ], string='Filter Period', default='today')

    filter_start_date = fields.Date(string='Filter Start Date')
    filter_end_date = fields.Date(string='Filter End Date')

    @api.model
    def get_current_user_info(self):
        """Retorna la información del usuario actual"""
        user = self.env.user
        return {
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email or user.login,
            'user_login': user.login,
            'company_id': user.company_id.id,
            'company_name': user.company_id.name,
            'filter_period': user.filter_period,
            'filter_start_date': user.filter_start_date and str(user.filter_start_date) or False,
            'filter_end_date': user.filter_end_date and str(user.filter_end_date) or False,
        }

    @api.model
    def save_user_filter(self, filter_data):
        """Guarda las preferencias de filtro del usuario actual"""
        try:
            _logger.info(f"save_user_filter called with data type: {type(filter_data)}, value: {filter_data}")

            # Si filter_data es una lista, tomar el primer elemento
            if isinstance(filter_data, list) and len(filter_data) > 0:
                filter_data = filter_data[0]

            # Si es un diccionario, extraer los valores
            if isinstance(filter_data, dict):
                period = filter_data.get('period', 'today')
                start_date = filter_data.get('startDate')
                end_date = filter_data.get('endDate')
            else:
                # Si no es un diccionario, usar valores por defecto
                _logger.warning(f"filter_data no es un diccionario: {type(filter_data)}")
                period = 'today'
                start_date = None
                end_date = None

            # Convertir fechas a string si es necesario
            if start_date:
                if isinstance(start_date, str):
                    start_date = start_date[:10]
                else:
                    start_date = str(start_date)[:10]

            if end_date:
                if isinstance(end_date, str):
                    end_date = end_date[:10]
                else:
                    end_date = str(end_date)[:10]

            _logger.info(f"Saving filter - Period: {period}, Start: {start_date}, End: {end_date}")

            # Actualizar el usuario actual usando sudo() para evitar problemas de permisos
            self.env.user.sudo().write({
                'filter_period': period,
                'filter_start_date': start_date if start_date else False,
                'filter_end_date': end_date if end_date else False,
            })

            return {
                'success': True,
                'message': 'Filter saved successfully',
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
            }
        except Exception as e:
            _logger.error(f"Error in save_user_filter: {str(e)}")
            _logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

    def get_date_range_from_filter(self):
        """Obtiene el rango de fechas basado en las preferencias guardadas"""
        self.ensure_one()

        if self.filter_period == 'custom':
            return {
                'start_date': self.filter_start_date,
                'end_date': self.filter_end_date,
            }

        today = fields.Date.today()

        if self.filter_period == 'today':
            return {'start_date': today, 'end_date': today}
        elif self.filter_period == 'yesterday':
            yesterday = today - timedelta(days=1)
            return {'start_date': yesterday, 'end_date': yesterday}
        elif self.filter_period == 'this_week':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            return {'start_date': start, 'end_date': end}
        elif self.filter_period == 'last_week':
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            return {'start_date': start, 'end_date': end}
        elif self.filter_period == 'this_month':
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return {'start_date': start, 'end_date': end}
        elif self.filter_period == 'last_month':
            if today.month == 1:
                start = today.replace(year=today.year - 1, month=12, day=1)
                end = today.replace(month=1, day=1) - timedelta(days=1)
            else:
                start = today.replace(month=today.month - 1, day=1)
                end = today.replace(day=1) - timedelta(days=1)
            return {'start_date': start, 'end_date': end}
        elif self.filter_period == 'this_year':
            return {
                'start_date': today.replace(month=1, day=1),
                'end_date': today.replace(month=12, day=31)
            }
        elif self.filter_period == 'last_year':
            return {
                'start_date': today.replace(year=today.year - 1, month=1, day=1),
                'end_date': today.replace(year=today.year - 1, month=12, day=31)
            }

        # Default: este mes
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return {'start_date': start, 'end_date': end}