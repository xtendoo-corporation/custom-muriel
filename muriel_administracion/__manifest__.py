{
    'name': 'Muriel Custom',
    'version': '18.0.1.0.1',
    'category': 'Extra Tools',
    'author': 'Abraham Carrasco (Xtendoo)',
    'website': '',
    'license': 'LGPL-3',
    'summary': 'Customización para Muriel',
    'images': [],
    'depends': [
        'contract',
        'stock',
        'contract_sale_generation',
    ],
    'data': [
        'views/stock_picking_views_inherit.xml',
        'views/report_invoice_custom.xml',
        'views/stock_move_views.xml',
        'views/contract.xml',
        'views/view_picking_form.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'muriel_administracion/static/src/scss/sale_portal.scss',
            # 'muriel_administracion/static/src/xml/button_box.xml',
            # 'muriel_administracion/static/src/xml/cog_menu.xml',
            'muriel_administracion/static/src/xml/control_panel.xml',

        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
}
