# -*- coding: utf-8 -*-
{
    "name": "APN - Pilates Suite",
    "summary": "",
    "description": "",
    "author": "IdooGroup",
    "website": "https://www.idoogroup.com",
    "license": "LGPL-3",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "",
    "version": "18.0.0.0.0",
    # any module necessary for this one to work correctly
    "depends": [
        ## MODULOS BASE
        "base", # 1. Módulos base fundamentales
        "web",
        "auth_signup",# 2. Módulos de autenticación y usuarios
        "auth_oauth",
        "mail",# 3. Módulos de mensajería y comunicación
        "base_geolocalize",# 4. Módulos de geolocalización
        "contacts",# 5. Módulos de contactos
        "product",# 6. Módulos de producto e inventario
        "stock",
        "sales_team",# 7. Módulos de ventas y equipos
        "sale",
        "sale_management",
        "sale_stock",
        "account",# 8. Módulos financieros
        "loyalty",# 9. Módulos de fidelización y pagos
        "payment",
        "rating",# 10. Módulos de valoraciones

        ## MODULOS OCA
        "base_multi_company",# 11. Módulos multi-compañía de OCA
        "product_multi_company",
        "web_responsive", # 12. Módulos de interfaz

        ## MODULOS IDOOGROUP
        "apn_theme",
        "apn_group",
        "apn_charts",
        "apn_company",
        "apn_notifications",
        "apn_api",
    ],
    # always loaded
    "data": [
        "data/system_parameter_data.xml",
        "views/views_login.xml",
        "views/views_dashboard.xml",
        "views/menu_icons.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "apn_suite/static/src/js/favicon.js",
            "apn_suite/static/src/css/dashboard.css",
            "apn_suite/static/src/css/card_info_build_construction.css",
            'apn_suite/static/src/css/kpi_cards.css',
            "apn_suite/static/src/js/card_info_build_construction.js",
            "apn_suite/static/src/js/date_filter_component.js",
            'apn_suite/static/src/js/kpi_card.js',
            'apn_suite/static/src/js/occupancy_card.js',
            'apn_suite/static/src/js/revenue_card.js',
            'apn_suite/static/src/js/classes_card.js',
            'apn_suite/static/src/js/new_clients_card.js',
            'apn_suite/static/src/js/card_info_distribution_revenue.js',
            "apn_suite/static/src/js/card_info_most_demand_classes.js",
            "apn_suite/static/src/js/card_info_weekly_attendance_trend.js",
            "apn_suite/static/src/js/dashboard.js",
            "apn_suite/static/src/xml/card_info_build_construction.xml",
            "apn_suite/static/src/xml/date_filter_component.xml",
            'apn_suite/static/src/xml/kpi_card.xml',
            'apn_suite/static/src/xml/occupancy_card.xml',
            'apn_suite/static/src/xml/revenue_card.xml',
            'apn_suite/static/src/xml/classes_card.xml',
            'apn_suite/static/src/xml/new_clients_card.xml',
            'apn_suite/static/src/xml/card_info_distribution_revenue.xml',
            "apn_suite/static/src/xml/card_info_most_demand_classes.xml",
            "apn_suite/static/src/xml/card_info_weekly_attendance_trend.xml",
            "apn_suite/static/src/xml/dashboard.xml",
        ],
        "web.assets_frontend": [
            "apn_suite/static/src/css/login.css",
            "apn_suite/static/src/js/hide_login_elements.js",
            "apn_suite/static/src/js/favicon.js",

        ],
        "web._assets_primary_variables": [],
    },
    # only loaded in demonstration mode
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
    "post_init_hook": "post_init_hook",
    "post_update_hook": "post_update_hook",
}