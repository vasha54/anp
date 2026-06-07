# -*- coding: utf-8 -*-
{
    'name': "APN - Pilates Charts",

    "summary": "",
    "description": "",
    "author": "IdooGroup",
    "website": "https://www.idoogroup.com",
    "license": "LGPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '18.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web'
    ],

    # always loaded
    'data': [],
    # only loaded in demonstration mode
    'demo': [],
    "assets": {
        "web.assets_backend": [
            
            "apn_charts/static/lib/chart.js/chart.umd.min.js",
            "apn_charts/static/src/js/bar_chart.js",
            "apn_charts/static/src/js/bubble_chart.js",
            "apn_charts/static/src/js/donut_chart.js",
            "apn_charts/static/src/js/line_chart.js",
            "apn_charts/static/src/js/multiline_chart.js",
            "apn_charts/static/src/js/pie_chart.js",
            "apn_charts/static/src/js/polar_area_chart.js",
            "apn_charts/static/src/js/radal_chart.js",
            "apn_charts/static/src/js/scatter_chart.js",
            "apn_charts/static/src/js/stacked_bar_chart.js",
            "apn_charts/static/src/js/area_chart.js",
            "apn_charts/static/src/js/multiarea_chart.js",
            "apn_charts/static/src/xml/bar_chart.xml",
            "apn_charts/static/src/xml/bubble_chart.xml",
            "apn_charts/static/src/xml/donut_chart.xml",
            "apn_charts/static/src/xml/line_chart.xml",
            "apn_charts/static/src/xml/multiline_chart.xml",
            "apn_charts/static/src/xml/pie_chart.xml",
            "apn_charts/static/src/xml/polar_area_chart.xml",
            "apn_charts/static/src/xml/radal_chart.xml",
            "apn_charts/static/src/xml/scatter_chart.xml",
            "apn_charts/static/src/xml/stacked_bar_chart.xml",
            "apn_charts/static/src/xml/area_chart.xml",
             "apn_charts/static/src/xml/multiarea_chart.xml",
            
        ],
        "web._assets_primary_variables": [
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
    "sequence": 1,
}

