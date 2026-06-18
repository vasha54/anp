{
    "name": "APN - Pilates Events",
    "version": "18.0.0.0.0",
    'depends': [
        'base',
        'web',
        'event',
        'event_product',
        'apn_group',
    ],
    'post_init_hook': 'adjust_addons_parents',
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}