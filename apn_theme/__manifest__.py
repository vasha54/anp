{
    "name": "APN - Pilates Theme",
    "summary": "Tema base APN Pilates Suite - Paleta corporativa",
    "description": """
        Tema personalizado con paleta de colores:
        Paleta: #F4A300 | #4A4A4A | #FFFFFF
    """,
    "author": "IdooGroup",
    "website": "https://www.idoogroup.com",
    "license": "LGPL-3",
    "category": "Theme/Corporate",
    "version": "18.0.0.0.1",
    "depends": [
        "web",
    ],
    "data": [
        # "views/assets.xml",
        # "views/templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "apn_theme/static/src/scss/theme_apn_classic.scss",
        ],
        "web.assets_frontend": [
            "apn_theme/static/src/scss/theme_apn_classic.scss",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}