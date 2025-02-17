from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    previous_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Entrega Anterior',
        compute='_compute_previous_picking_id'
    )

    @api.depends('partner_id')
    def _compute_previous_picking_id(self):
        for picking in self:
            previous_picking = self.env['stock.picking'].search([
                ('partner_id', '=', picking.partner_id.id),
                ('id', '!=', picking.id),
                ('state', '=', 'done'),
                ('picking_type_id', '=', picking.picking_type_id.id),
                ('date_done', '<', picking.date_done)
            ], limit=1, order='date_done desc')
            picking.previous_picking_id = previous_picking
