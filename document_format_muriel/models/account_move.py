from odoo import models
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_grouped_lines(self):
        """
        Agrupa las líneas de factura por producto.
        Usa el amount_untaxed de la factura para garantizar precisión.
        """
        grouped = defaultdict(lambda: {
            'name': '',
            'quantity': Decimal('0.0'),
            'product_uom_name': '',
            'price_unit': Decimal('0.0'),
            'discount': Decimal('0.0'),
            'tax_names': set(),
            'price_subtotal': Decimal('0.0'),
            'lines': []
        })

        # Usar invoice_line_ids y filtrar por producto
        lines = self.invoice_line_ids.filtered(lambda l: l.product_id)

        # Obtener el total sin impuestos directamente de la factura
        # Este es el valor exacto que aparece como "Base imponible"
        total_untaxed = Decimal(str(self.amount_untaxed))

        for line in lines:
            # Usar product_id como clave para agrupar
            key = line.product_id.id

            if not grouped[key]['name']:
                grouped[key]['name'] = line.name
                grouped[key]['product_uom_name'] = line.product_uom_id.name if line.product_uom_id else ''
                grouped[key]['discount'] = Decimal(str(line.discount)) if line.discount else Decimal('0.0')

            # Guardar referencia a la línea
            grouped[key]['lines'].append(line)

            # Acumular cantidad usando Decimal
            grouped[key]['quantity'] += Decimal(str(line.quantity))

            # Recopilar nombres de impuestos
            for tax in line.tax_ids:
                grouped[key]['tax_names'].add(tax.name)

        # Convertir a lista y calcular el precio unitario ajustado
        result = []

        # Si solo hay un producto agrupado, usar directamente el amount_untaxed
        if len(grouped) == 1:
            for key, data in grouped.items():
                # Usar el total exacto de la factura
                price_subtotal = total_untaxed

                # Calcular el precio unitario basándose en el total exacto
                if data['quantity'] > 0:
                    price_unit_efectivo = price_subtotal / data['quantity']
                    # Redondear a 4 decimales para mantener precisión
                    price_unit_efectivo = price_unit_efectivo.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                else:
                    price_unit_efectivo = Decimal('0.0')

                result_item = {
                    'name': data['name'],
                    'quantity': float(data['quantity']),
                    'product_uom_name': data['product_uom_name'],
                    'price_unit': float(price_unit_efectivo),
                    'discount': float(data['discount']),
                    'tax_names': list(data['tax_names']),
                    'price_subtotal': float(price_subtotal)  # Usar el total exacto
                }
                result.append(result_item)
        else:
            # Si hay múltiples productos, distribuir proporcionalmente
            # Primero calcular el total de las líneas originales
            total_lines = sum(Decimal(str(line.price_subtotal)) for line in lines)

            for key, data in grouped.items():
                # Calcular el subtotal de este grupo
                group_subtotal = sum(Decimal(str(l.price_subtotal)) for l in data['lines'])

                # Distribuir el total real proporcionalmente
                if total_lines > 0:
                    price_subtotal = (group_subtotal / total_lines) * total_untaxed
                else:
                    price_subtotal = Decimal('0.0')

                # Calcular el precio unitario
                if data['quantity'] > 0:
                    price_unit_efectivo = price_subtotal / data['quantity']
                    price_unit_efectivo = price_unit_efectivo.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                else:
                    price_unit_efectivo = Decimal('0.0')

                # Redondear el subtotal a 2 decimales
                price_subtotal = price_subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                result_item = {
                    'name': data['name'],
                    'quantity': float(data['quantity']),
                    'product_uom_name': data['product_uom_name'],
                    'price_unit': float(price_unit_efectivo),
                    'discount': float(data['discount']),
                    'tax_names': list(data['tax_names']),
                    'price_subtotal': float(price_subtotal)
                }
                result.append(result_item)

        return result
