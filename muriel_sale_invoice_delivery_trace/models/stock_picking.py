from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return = fields.Boolean(
        string='Es Devolución',
        compute='_compute_is_return',
        store=False
    )

    picking_type_label = fields.Char(
        string='Tipo de Operación',
        compute='_compute_picking_type_label'
    )

    @api.depends('origin')
    def _compute_is_return(self):
        for picking in self:
            picking.is_return = picking.origin and (
                'Return of ' in picking.origin or
                'Devolución de ' in picking.origin or
                'Retorno de ' in picking.origin
            )

    @api.depends('is_return')
    def _compute_picking_type_label(self):
        for picking in self:
            picking.picking_type_label = 'Devolución' if picking.is_return else 'Entrega'
