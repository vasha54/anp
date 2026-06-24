import odoo
import re
import logging
import json

from datetime import datetime, timedelta
from user_agents import parse

from odoo import _, http
from odoo.http import Response, request
from odoo.exceptions import AccessDenied
from odoo.modules.registry import Registry

from ..base_api_controller import BaseAPIController

_logger = logging.getLogger(__name__)


class MobileVersionAPIController(BaseAPIController):

    # ------------------ Plataformas ------------------
    @http.route('/api_pilates/v1/mobile_get_platforms', type='json', auth='none', methods=['POST'])
    def get_platforms(self, **kwargs):
        """
        Obtiene todas las plataformas activas.
        POST sin argumentos.
        """
        try:
            data = request.env['mobile.platform'].sudo().get_platforms()
            response = {
                'status': 'success',
                'message': _('Data obtained successfully.'),
                'data': data,
            }
            return response
        except Exception as e:
            return self._handle_error(e)

    # ------------------ Versiones (métodos originales) ------------------
    @http.route('/api_pilates/v1/mobile_get_versions', type='json', auth='none', methods=['POST'])
    def get_versions(self, **kwargs):
        """
        Obtiene todas las versiones, opcionalmente filtradas por código de plataforma.
        Argumentos JSON: { "platform_code": "ios" } (opcional)
        """
        try:
            data = self._get_json_data(request.httprequest.data)
            platform_code = data.get('platform_code',None)
            data = request.env['mobile.version'].sudo().get_versions(platform_code=platform_code)
            response = {
                'status': 'success',
                'message': _('Data obtained successfully.'),
                'data': data,
            }
            return response
        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/mobile_get_latest_version', type='json', auth='none', methods=['POST'])
    def get_latest_version(self, **kwargs):
        """
        Obtiene la última versión de una plataforma.
        Argumentos JSON: { "platform_code": "android" }
        """
        try:
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['platform_code'], data)
            platform_code = data.get('platform_code', None)
            data = request.env['mobile.version'].sudo().get_latest_version(platform_code)
            response = {
                'status': 'success',
                'message': _('Data obtained successfully.'),
                'data': data,
            }
            return response
        except Exception as e:
            return self._handle_error(e)

    # ------------------ Nuevos métodos de filtrado por compañía ------------------
    @http.route('/api_pilates/v1/mobile_get_versions_by_company', type='json', auth='none', methods=['POST'])
    def get_versions_by_company(self, **kwargs):
        """
        Todas las versiones de una compañía.
        Argumentos JSON: { "company_id": 1 }
        """
        try:
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['company_id'],data)
            company_id = data.get('company_id')
            company = request.env['res.company'].sudo().search([('id','=',company_id),('is_branch','=',False)],limit=1)
            if not company:
                raise Exception(_(f"Not found company with id: {company_id}"))

            data = request.env['mobile.version'].sudo().get_versions_by_company(company_id)
            response = {
                'status': 'success',
                'message': _('Data obtained successfully.'),
                'data': data,
            }
            return response
        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/mobile_get_versions_by_company_and_platform', type='json', auth='none', methods=['POST'])
    def get_versions_by_company_and_platform(self, **kwargs):
        """
        Todas las versiones de una compañía y plataforma.
        Argumentos JSON: { "company_id": 1, "platform_code": "ios" }
        """
        try:
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['company_id', 'platform_code'], data)
            company_id = data.get('company_id')
            platform_code = data.get('platform_code')
            company = request.env['res.company'].sudo().search([('id','=',company_id),('is_branch','=',False)],limit=1)
            if not company:
                raise Exception(_(f"Not found company with id: {company_id}"))

            data = request.env['mobile.version'].sudo().get_versions_by_company_and_platform(company_id, platform_code)
            response = {
                'status': 'success',
                'message': _('Data obtained successfully.'),
                'data': data,
            }
            return response
        except Exception as e:
            return self._handle_error(e)


    @http.route('/api_pilates/v1/mobile_get_latest_versions_by_company', type='json', auth='none', methods=['POST'])
    def get_latest_versions_by_company(self, **kwargs):
        """
        Última versión de cada plataforma para una compañía.
        Argumentos JSON: { "company_id": 1 }
        """
        try:
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['company_id'], data)
            company_id = data.get('company_id')
            company = request.env['res.company'].sudo().search([('id','=',company_id),('is_branch','=',False)],limit=1)
            if not company:
                raise Exception(_(f"Not found company with id: {company_id}"))

            data = request.env['mobile.version'].sudo().get_latest_versions_by_company(company_id)
            response = {
                'status': 'success',
                'message': _('Data obtained successfully.'),
                'data': data,
            }
            return response
        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/mobile_get_latest_version_by_company_and_platform', type='json', auth='none', methods=['POST'])
    def get_latest_version_by_company_and_platform(self, **kwargs):
        """
        Última versión de una plataforma en una compañía.
        Argumentos JSON: { "company_id": 1, "platform_code": "huawei" }
        """
        try:
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['company_id', 'platform_code'], data)
            company_id = data.get('company_id')
            platform_code = data.get('platform_code')
            company = request.env['res.company'].sudo().search([('id','=',company_id),('is_branch','=',False)],limit=1)
            if not company:
                raise Exception(_(f"Not found company with id: {company_id}"))

            data = request.env['mobile.version'].sudo().get_latest_version_by_company_and_platform(company_id, platform_code)
            response = {
                'status': 'success',
                'message': _('Data obtained successfully.'),
                'data': data,
            }
            return response
        except Exception as e:
            return self._handle_error(e)
