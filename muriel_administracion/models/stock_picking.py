from odoo import models, fields, api
from odoo.exceptions import UserError

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

    def action_view_previous_picking(self):
        self.ensure_one()
        if not self.previous_picking_id:
            raise UserError('No hay una entrega anterior.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Previous Picking',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.previous_picking_id.id,
            'target': 'current',
        }
