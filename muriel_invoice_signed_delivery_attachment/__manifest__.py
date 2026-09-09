# -*- coding: utf-8 -*-
{
    'name': 'Muriel - Adjuntar Albaranes Firmados a Factura',
    'version': '18.0.1.0.0',
    'summary': 'Adjunta automáticamente los albaranes de entrega firmados por el cliente al enviar una factura por email',
    'description': '''
        Al enviar una factura de cliente por correo (envío individual, envío
        masivo o cron de envío automático), este módulo adjunta al mismo
        email todos los albaranes de entrega relacionados que hayan sido
        firmados por el cliente.
    ''',
    'category': 'Accounting/Accounting',
    'author': 'Dani Domínguez',
    'website': 'https://www.xtendoo.es',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'sale_stock',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
