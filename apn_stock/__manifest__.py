{
    "name": "APN - Pilates Stock",
    "version": "18.0.0.0.0",
    'depends': [
        'base',
        'web',
        'stock',
    ],
    'post_init_hook': 'adjust_addons_parents',
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}