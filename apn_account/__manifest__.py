# -*- coding: utf-8 -*-
{
    'name': "APN - Pilates Account",
    'depends': [
        'base',
        'account',
    ],
    'post_init_hook': 'adjust_addons_parents',
    'installable': True,
    'application': True,
    'sequence': 1,
}
