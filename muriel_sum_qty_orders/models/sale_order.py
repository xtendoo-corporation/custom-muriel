# -*- coding: utf-8 -*-
from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_reportable_order_lines(self):
        return self.mapped('order_line').filtered(
            lambda line: not line.display_type and line.product_id
        )

    def _prepare_total_qty_report_data(self):
        product_totals_map = {}
        total_qty = 0.0

        for line in self._get_reportable_order_lines():
            product = line.product_id
            qty_in_product_uom = line.product_uom._compute_quantity(
                line.product_uom_qty,
                product.uom_id,
            )
            total_qty += qty_in_product_uom

            product_total = product_totals_map.setdefault(product.id, {
                'product_id': product.id,
                'product_name': product.display_name,
                'uom_name': product.uom_id.name,
                'total_qty': 0.0,
            })
            product_total['total_qty'] += qty_in_product_uom

        product_totals = sorted(
            product_totals_map.values(),
            key=lambda product_total: product_total['product_name'],
        )

        return {
            'selected_order_count': len(self),
            'selected_line_count': len(self._get_reportable_order_lines()),
            'selected_product_count': len(product_totals),
            'total_qty': total_qty,
            'product_totals': product_totals,
        }

    @api.model
    def action_print_total_qty(self, ids=None):
        """Imprime el informe con la suma de cantidades de los pedidos seleccionados.

        En Odoo 18, los botones `type="object"` en selección múltiple llaman al
        método sobre el modelo y pasan la lista de ids como primer argumento.
        """
        orders = self.env['sale.order'].browse(ids or self.env.context.get('active_ids') or []).exists()

        if not orders:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Atención'),
                    'message': _('Seleccione al menos un pedido para imprimir la suma de cantidades.'),
                    'sticky': False,
                    'type': 'warning',
                },
            }

        data = orders._prepare_total_qty_report_data()
        return self.env.ref('muriel_sum_qty_orders.action_report_total_qty').report_action(
            orders,
            data=data,
        )

