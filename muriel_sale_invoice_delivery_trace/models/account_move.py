from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    related_sale_order_ids = fields.Many2many(
        'sale.order',
        string='Pedidos de Venta Relacionados',
        compute='_compute_related_sale_orders',
        store=False
    )

    related_sale_count = fields.Integer(
        string='Número de Pedidos',
        compute='_compute_related_sale_orders'
    )

    @api.depends('invoice_line_ids', 'invoice_line_ids.sale_line_ids', 'invoice_origin')
    def _compute_related_sale_orders(self):
        for move in self:
            sale_orders = self.env['sale.order']

            # 1. Buscar por líneas de factura relacionadas con líneas de venta
            sale_orders |= move.invoice_line_ids.mapped('sale_line_ids.order_id')

            # 2. Buscar por origen de factura
            if move.invoice_origin:
                origin_orders = self.env['sale.order'].search([
                    ('name', 'in', move.invoice_origin.split(', '))
                ])
                sale_orders |= origin_orders

            # 3. Fallback: Buscar por cliente y líneas facturadas
            if not sale_orders and move.commercial_partner_id:
                potential_orders = self.env['sale.order'].search([
                    ('partner_id.commercial_partner_id', '=', move.commercial_partner_id.id),
                    ('state', 'in', ['sale', 'done']),
                    ('invoice_status', '=', 'invoiced')
                ])
                for order in potential_orders:
                    if any(line.invoice_lines for line in order.order_line):
                        sale_orders |= order

            move.related_sale_order_ids = sale_orders
            move.related_sale_count = len(sale_orders)

    def action_view_related_sales(self):
        self.ensure_one()
        return {
            'name': 'Pedidos de Venta Relacionados',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.related_sale_order_ids.ids)],
            'context': {'create': False}
        }
