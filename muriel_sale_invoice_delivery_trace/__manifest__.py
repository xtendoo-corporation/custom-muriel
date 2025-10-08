{
    "name": "Muriel - Trazabilidad Facturas-Ventas-Entregas",
    "summary": "Trazabilidad completa entre Facturas, Pedidos y Entregas con exportación Excel",
    "version": "18.0.1.0.0",
    "category": "Sales/Reporting",
    "website": "https://www.xtendoo.es",
    "author": "Xtendoo",
    "license": "LGPL-3",
    "depends": [
        "sale_management",
        "account",
        "stock"
    ],
    "external_dependencies": {
        "python": ["xlsxwriter"]
    },
    "data": [
        "views/trace_views.xml",
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "security/ir.model.access.csv",
        "views/wizard_views.xml",
        "views/menuitems.xml"
    ],
    "installable": True,
    "application": False,
}

