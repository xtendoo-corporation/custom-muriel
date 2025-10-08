{
    "name": "Muriel - Invoice ↔ Sales ↔ Delivery Trace (Excel)",
    "summary": "Trazabilidad Facturas de Cliente ↔ Pedidos de Venta ↔ Entregas/Devoluciones con exportación a Excel",
    "version": "18.0.1.0.0",
    "author": "Muriel / Xtendoo",
    "website": "https://xtd.es",
    "license": "LGPL-3",
    "category": "Sales/Accounting",
    "depends": ["sale_management", "account", "stock"],
    "external_dependencies": {
        "python": ["xlsxwriter"]
    },
    "data": [
        "security/ir.model.access.csv",
        "views/menuitems.xml",
        "views/wizard_views.xml",
        "views/account_move_views.xml",
        "views/sale_order_views.xml",
        "views/stock_picking_views.xml",
        "views/trace_views.xml"
    ],
    "installable": True,
    "application": False,
}

