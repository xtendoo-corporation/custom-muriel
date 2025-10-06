{
    'name': 'Document Format Muriel',
    'version': '18.0.1.0.0',
    'author': 'Guillermo Bárcena López',
    'category': 'Customization',
    'summary': 'Personalización de formatos de documentos con agrupación de líneas',
    'description': '''
        Este módulo permite personalizar los formatos de documentos como facturas.
        Características:
        - Agrupa líneas de factura del mismo producto y precio
    ''',
    'depends': [
        'account',
        'base',
    ],
    'data': [
        'views/invoice_document.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
