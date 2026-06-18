{
    "name": "APN - Pilates Sale",
    "version": "18.0.0.0.0",
    'depends': [
        'base',
        'web',
        'sale',
        'sale_management',
        'sale_stock',
    ],
    'post_init_hook': 'adjust_addons_parents',
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}