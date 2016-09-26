# -*- coding: utf-8 -*-
{
    'name': "Consignor Shipping",
    'description': "Send your shippings through Consignor and track them online",
    'author': "TinderBox AS",
    'website': "http://tinderbox.no",
    'category': 'Sales Management',
    'version': '1.0',
    'depends': ['delivery', 'mail'],
    'data': [
        'data/delivery_consignor.xml',
        'views/delivery_consignor.xml',
    ],
    'application': True,
    'installable': True,
}