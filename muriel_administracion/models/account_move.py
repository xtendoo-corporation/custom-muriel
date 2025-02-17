from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'


    def get_combined_invoice_lines(self):
        combined_lines = {}
        for line in self.invoice_line_ids:
            key = (line.product_id.id, line.price_unit, line.tax_ids)
            if key in combined_lines:
                combined_lines[key]['quantity'] += line.quantity
                combined_lines[key]['price_subtotal'] += line.price_subtotal
            else:
                combined_lines[key] = {
                    'product_id': line.product_id,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'price_subtotal': line.price_subtotal,
                    'tax_ids': line.tax_ids,
                    'currency_id': line.currency_id.id,
                }

        # Solo por depuración
        print("Combinadas:", combined_lines)

        combined_lines_list = []
        for values in combined_lines.values():
            combined_line = self.env['account.move.line'].new(values)
            combined_lines_list.append(combined_line)

        return combined_lines_list
