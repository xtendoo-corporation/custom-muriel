from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    related_picking_ids = fields.Many2many(
        'stock.picking',
        compute='_compute_related_pickings',
        string='Entregas y Devoluciones',
        store=False
    )

    picking_count = fields.Integer(
        string='Número de Entregas/Devoluciones',
        compute='_compute_related_pickings'
    )

    @api.depends('procurement_group_id', 'picking_ids')
    def _compute_related_pickings(self):
        for order in self:
            pickings = self.env['stock.picking']
            if order.procurement_group_id:
                pickings = self.env['stock.picking'].search([
                    ('group_id', '=', order.procurement_group_id.id),
                    ('state', '=', 'done'),
                    ('picking_type_id.code', '=', 'outgoing')
                ])

                # Buscar devoluciones relacionadas
                for picking in pickings:
                    returns = self.env['stock.picking'].search([
                        ('origin', 'ilike', f'Return of {picking.name}'),
                        ('state', '=', 'done')
                    ])
                    pickings |= returns

            order.related_picking_ids = pickings
            order.picking_count = len(pickings)

    def action_view_deliveries(self):
        self.ensure_one()
        return {
            'name': 'Entregas y Devoluciones',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.related_picking_ids.ids)],
            'context': {
                'create': False,
                'show_picking_type': True
            }
        }
