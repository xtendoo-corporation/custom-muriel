from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campos relacionados con Pedidos de Venta
    related_sale_order_ids = fields.Many2many(
        'sale.order',
        string='Pedidos de Venta Relacionados',
        compute='_compute_related_sale_orders',
        store=True
    )

    related_sale_count = fields.Integer(
        string='Número de Pedidos',
        compute='_compute_related_sale_orders',
        store=True
    )

    related_sale_names = fields.Char(
        string='Pedidos',
        compute='_compute_related_sale_orders',
        store=True
    )

    # Campos relacionados con Albaranes
    related_picking_ids = fields.Many2many(
        'stock.picking',
        string='Albaranes Relacionados',
        compute='_compute_related_pickings',
        store=True
    )

    related_picking_count = fields.Integer(
        string='Número de Albaranes',
        compute='_compute_related_pickings',
        store=True
    )

    related_picking_names = fields.Char(
        string='Albaranes',
        compute='_compute_related_pickings',
        store=True
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.sale_line_ids', 'invoice_origin')
    def _compute_related_sale_orders(self):
        for move in self:
            sale_orders = self.env['sale.order']

            # Solo procesar facturas de cliente
            if move.move_type not in ('out_invoice', 'out_refund'):
                move.related_sale_order_ids = sale_orders
                move.related_sale_count = 0
                move.related_sale_names = ''
                continue

            # 1. Buscar por líneas de factura relacionadas con líneas de venta
            for line in move.invoice_line_ids:
                if line.sale_line_ids:
                    sale_orders |= line.sale_line_ids.mapped('order_id')

            # 2. Buscar por origen de factura
            if move.invoice_origin:
                origins = [o.strip() for o in move.invoice_origin.split(',')]
                origin_orders = self.env['sale.order'].search([
                    ('name', 'in', origins)
                ])
                sale_orders |= origin_orders

            # 3. Fallback: Buscar por cliente
            if not sale_orders and move.commercial_partner_id:
                potential_orders = self.env['sale.order'].search([
                    ('partner_id.commercial_partner_id', '=', move.commercial_partner_id.id),
                    ('state', 'in', ['sale', 'done']),
                    ('invoice_status', 'in', ['invoiced', 'to invoice'])
                ], limit=10)

                for order in potential_orders:
                    # Verificar si alguna línea del pedido está en la factura
                    for order_line in order.order_line:
                        if order_line.invoice_lines & move.invoice_line_ids:
                            sale_orders |= order
                            break

            _logger.info(f"Factura {move.name}: {len(sale_orders)} pedidos encontrados: {sale_orders.mapped('name')}")

            move.related_sale_order_ids = sale_orders
            move.related_sale_count = len(sale_orders)
            move.related_sale_names = ', '.join(sale_orders.mapped('name')) if sale_orders else ''

    @api.depends('related_sale_order_ids', 'related_sale_order_ids.picking_ids')
    def _compute_related_pickings(self):
        for move in self:
            pickings = self.env['stock.picking']

            # Obtener todos los albaranes de los pedidos relacionados
            for sale in move.related_sale_order_ids:
                pickings |= sale.picking_ids

            _logger.info(f"Factura {move.name}: {len(pickings)} albaranes encontrados: {pickings.mapped('name')}")

            move.related_picking_ids = pickings
            move.related_picking_count = len(pickings)
            move.related_picking_names = ', '.join(pickings.mapped('name')) if pickings else ''

    def action_view_related_sales(self):
        """Acción para ver los pedidos de venta relacionados"""
        self.ensure_one()
        return {
            'name': 'Pedidos de Venta Relacionados',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.related_sale_order_ids.ids)],
            'context': {'create': False}
        }

    def action_view_related_pickings(self):
        """Acción para ver los albaranes relacionados"""
        self.ensure_one()
        return {
            'name': 'Albaranes Relacionados',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.related_picking_ids.ids)],
            'context': {'create': False}
        }
