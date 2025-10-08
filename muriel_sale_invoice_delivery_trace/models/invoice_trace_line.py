from odoo import models, fields, api


class InvoiceTraceLine(models.TransientModel):
    _name = 'invoice.trace.line'
    _description = 'Línea de Trazabilidad de Factura'
    _order = 'invoice_date desc, invoice_id, product_id'

    # Datos de la factura
    invoice_id = fields.Many2one('account.move', string='Factura', readonly=True)
    invoice_name = fields.Char(string='Número Factura', readonly=True)
    invoice_date = fields.Date(string='Fecha Factura', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True)

    # Datos del producto/línea
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    product_name = fields.Char(string='Descripción', readonly=True)
    invoice_line_id = fields.Many2one('account.move.line', string='Línea Factura', readonly=True)

    # Cantidades - RENOMBRADAS
    quantity_invoiced = fields.Float(string='Total Facturado', readonly=True,
                                     help='Cantidad total facturada')
    quantity_delivered = fields.Float(string='Cantidad Enviada', readonly=True,
                                      help='Cantidad total enviada al cliente')
    quantity_returned = fields.Float(string='Cantidad Devuelta', readonly=True,
                                     help='Cantidad devuelta por el cliente')
    quantity_net = fields.Float(string='Cantidad Neta', readonly=True,
                                help='Cantidad Enviada - Cantidad Devuelta')

    # Pedidos y Albaranes
    sale_order_ids = fields.Many2many('sale.order', string='Pedidos', readonly=True)
    sale_order_names = fields.Char(string='Pedidos de Venta', readonly=True)

    picking_ids = fields.Many2many('stock.picking', string='Albaranes', readonly=True)
    delivery_names = fields.Char(string='Entregas', readonly=True)
    return_names = fields.Char(string='Devoluciones', readonly=True)

    # Valores monetarios
    price_unit = fields.Float(string='Precio Unitario', readonly=True)
    price_subtotal = fields.Float(string='Subtotal Facturado', readonly=True)
    price_total_net = fields.Float(string='Total Neto', readonly=True,
                                   help='Precio Unit. × Cantidad Neta')

    # Estado
    state = fields.Selection(related='invoice_id.state', string='Estado Factura', readonly=True)

    # Indicadores
    has_returns = fields.Boolean(string='Tiene Devoluciones', readonly=True)
    discrepancy = fields.Boolean(string='Discrepancia', readonly=True,
                                 help='Cantidad facturada diferente de cantidad neta')
