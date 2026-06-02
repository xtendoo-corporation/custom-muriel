# -*- coding: utf-8 -*-
{
    'name': 'Muriel - Suma cantidades pedidos',
    'version': '1.0.1',
    'summary': 'Botón en la lista de pedidos para imprimir la suma de cantidades de los pedidos seleccionados',
    'description': 'Añade un botón de acción masiva en la vista de lista de pedidos de venta para imprimir un informe con la suma total de cantidades de los pedidos seleccionados.',
    'category': 'Sales',
    'author': 'Muriel',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [
        'views/sale_order_views.xml',
        'report/report_total_qty.xml',
    ],
    'installable': True,
    'application': False,
}

