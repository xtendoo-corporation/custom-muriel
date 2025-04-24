from odoo import models, fields

class ContractContract(models.Model):
    _inherit = 'contract.contract'

    route_id = fields.Many2one(
        'stock.route',
        string='Ruta',
        help='Ruta aplicable a este contrato',
    )

    def _recurring_create_sale(self, date_ref=False):
        sale_orders = super()._recurring_create_sale(date_ref=date_ref)

        for sale in sale_orders:

            contract = self.search([('name', '=', sale.origin)], limit=1)

            if contract and contract.route_id:
                sale.write({'route_id': contract.route_id.id})
                for i, line in enumerate(sale.order_line):
                    line.write({'route_id': contract.route_id.id})

                sale.write({'date_order': sale.date_order})

        return sale_orders
