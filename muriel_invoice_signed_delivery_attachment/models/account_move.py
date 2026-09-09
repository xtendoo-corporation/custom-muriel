# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_signed_delivery_pickings(self):
        """Albaranes de entrega firmados por el cliente relacionados con esta factura."""
        self.ensure_one()
        if self.move_type not in ('out_invoice', 'out_refund'):
            return self.env['stock.picking']

        sale_orders = self.invoice_line_ids.sale_line_ids.order_id
        if not sale_orders and self.invoice_origin:
            origins = [origin.strip() for origin in self.invoice_origin.split(',')]
            sale_orders = self.env['sale.order'].search([('name', 'in', origins)])

        return sale_orders.picking_ids.filtered(
            lambda picking: picking.picking_type_id.code == 'outgoing'
            and picking.state == 'done'
            and picking.signature
        )
