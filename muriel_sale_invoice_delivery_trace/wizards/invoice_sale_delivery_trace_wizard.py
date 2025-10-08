from odoo import models, fields, api
from datetime import datetime
import xlsxwriter
import base64
import io


class InvoiceSaleDeliveryTraceWizard(models.TransientModel):
    _name = 'invoice.sale.delivery.trace.wizard'
    _description = 'Wizard de Trazabilidad de Facturas'

    date_from = fields.Date(string='Fecha Desde', required=True,
                            default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='Fecha Hasta', required=True,
                          default=fields.Date.today())
    company_id = fields.Many2one('res.company', string='Compañía',
                                 default=lambda self: self.env.company)
    partner_ids = fields.Many2many('res.partner', string='Clientes')
    product_ids = fields.Many2many('product.product', string='Productos')

    def action_generate_trace(self):
        self.ensure_one()

        print("\n" + "=" * 80)
        print("INICIANDO GENERACIÓN DE TRAZABILIDAD")
        print("=" * 80)
        print(f"Fecha desde: {self.date_from}")
        print(f"Fecha hasta: {self.date_to}")
        print(f"Compañía: {self.company_id.name}")

        # Limpiar registros anteriores del usuario
        old_records = self.env['invoice.trace.line'].search([])
        print(f"\nEliminando {len(old_records)} registros antiguos...")
        old_records.unlink()

        # Buscar facturas
        domain = [
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
            print(f"Filtrando por clientes: {self.partner_ids.mapped('name')}")

        invoices = self.env['account.move'].search(domain)
        print(f"\n✓ Facturas encontradas: {len(invoices)}")

        if not invoices:
            print("✗ NO HAY FACTURAS - Mostrando notificación")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No se encontraron facturas en el rango de fechas seleccionado.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Generar líneas de trazabilidad
        trace_lines = []
        for invoice in invoices:
            print(f"\n--- Procesando Factura: {invoice.name} ---")
            print(f"    Estado: {invoice.state}")
            print(f"    Fecha: {invoice.invoice_date}")
            print(f"    Cliente: {invoice.partner_id.name}")
            print(f"    Total líneas en factura: {len(invoice.invoice_line_ids)}")

            # Ver todas las líneas antes del filtro
            for idx, line in enumerate(invoice.invoice_line_ids):
                print(f"    Línea {idx + 1}:")
                print(f"      - Nombre: {line.name[:60]}")
                print(f"      - display_type: {repr(line.display_type)}")
                print(f"      - Producto: {line.product_id.name if line.product_id else 'SIN PRODUCTO'}")
                print(f"      - Cantidad: {line.quantity}")

            # Filtrar líneas
            # Filtrar líneas
            # CAMBIO AQUÍ: en Odoo 17, las líneas normales tienen display_type='product'
            filtered_lines = invoice.invoice_line_ids.filtered(
                lambda l: l.display_type not in ('line_section', 'line_note')
            )
            print(f"    ✓ Líneas después de filtrar (sin sección/nota): {len(filtered_lines)}")

            for inv_line in filtered_lines:
                print(f"\n    --> Procesando línea ID {inv_line.id}")
                print(f"        Producto: {inv_line.product_id.name if inv_line.product_id else 'N/A'}")
                print(f"        Cantidad: {inv_line.quantity}")

                # Filtrar por productos si se especificaron
                if self.product_ids and inv_line.product_id not in self.product_ids:
                    print(f"        ✗ FILTRADA - No está en productos seleccionados")
                    continue

                print(f"        ✓ Calculando trazabilidad...")
                trace_data = self._compute_trace_line_data(invoice, inv_line)
                trace_lines.append(trace_data)
                print(f"        ✓ Trazabilidad calculada y agregada")

        print(f"\n{'=' * 80}")
        print(f"TOTAL DE LÍNEAS DE TRAZABILIDAD GENERADAS: {len(trace_lines)}")
        print(f"{'=' * 80}\n")

        if not trace_lines:
            print("✗ NO SE GENERARON LÍNEAS - Mostrando notificación")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No se encontraron líneas para procesar. Verifica que las facturas tengan líneas con display_type=False.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Crear registros transitorios
        print(f"Creando {len(trace_lines)} registros en invoice.trace.line...")
        trace_records = self.env['invoice.trace.line'].create(trace_lines)
        print(f"✓ Registros creados: {len(trace_records)}")
        print(f"✓ IDs: {trace_records.ids}")

        return {
            'name': 'Trazabilidad Facturas-Ventas-Entregas',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.trace.line',
            'view_mode': 'list,pivot,graph',
            'views': [
                (self.env.ref('muriel_sale_invoice_delivery_trace.view_invoice_trace_line_tree').id, 'list'),
                (self.env.ref('muriel_sale_invoice_delivery_trace.view_invoice_trace_line_pivot').id, 'pivot'),
                (self.env.ref('muriel_sale_invoice_delivery_trace.view_invoice_trace_line_graph').id, 'graph'),
            ],
            'domain': [('id', 'in', trace_records.ids)],
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            },
            'target': 'current',
        }

    def _compute_trace_line_data(self, invoice, inv_line):
        """Calcula todos los datos de trazabilidad para una línea de factura"""

        print(f"          _compute_trace_line_data para línea {inv_line.id}")

        # Obtener pedidos de venta relacionados
        sale_orders = self.env['sale.order']
        if inv_line.sale_line_ids:
            sale_orders = inv_line.sale_line_ids.mapped('order_id')
            print(f"          Pedidos encontrados por sale_line_ids: {sale_orders.mapped('name')}")
        else:
            print(f"          ✗ No hay sale_line_ids en esta línea")

        # Obtener albaranes de los pedidos
        pickings = sale_orders.mapped('picking_ids')
        print(f"          Albaranes encontrados: {pickings.mapped('name')}")

        # Calcular cantidades entregadas y devueltas para este producto
        quantity_delivered = 0.0
        quantity_returned = 0.0
        delivery_pickings = []
        return_pickings = []

        for picking in pickings:
            if picking.state != 'done':
                print(f"          Picking {picking.name} estado: {picking.state} (no procesado)")
                continue

            # Buscar movimientos de este producto
            moves = picking.move_ids.filtered(
                lambda m: m.product_id == inv_line.product_id and m.state == 'done'
            )

            print(f"          Picking {picking.name}:")
            print(f"            picking_type_code: {picking.picking_type_code}")
            print(f"            picking_type_id.code: {picking.picking_type_id.code}")
            print(f"            origin: {picking.origin}")

            # DETECCIÓN CORRECTA DE DEVOLUCIÓN
            # Una devolución tiene picking_type_code = 'incoming' Y viene de un cliente
            # O tiene el campo return_id o el origin contiene 'Return'
            is_return = False


            if picking.picking_type_code == 'incoming' and picking.partner_id.id == invoice.partner_id.id:
                is_return = True

            if moves and moves[0].location_dest_id.usage == 'internal':
                # Si el destino es interno, verificamos el origen
                if moves[0].location_id.usage == 'customer':
                    is_return = True

            if picking.origin and 'Return' in picking.origin:
                is_return = True

            print(f"            ¿Es devolución?: {is_return}")
            print(f"            Movimientos encontrados: {len(moves)}")

            for move in moves:
                qty = move.quantity
                print(f"            Movimiento {move.id}:")
                print(f"              Producto: {move.product_id.name}")
                print(f"              Cantidad: {qty}")
                print(f"              Location origen: {move.location_id.name} ({move.location_id.usage})")
                print(f"              Location destino: {move.location_dest_id.name} ({move.location_dest_id.usage})")

                if is_return:
                    # Es una DEVOLUCIÓN (el cliente devuelve producto)
                    quantity_returned += qty
                    return_pickings.append(picking.name)
                    print(f"              → DEVOLUCIÓN acumulada: {quantity_returned}")
                else:
                    # Es una ENTREGA normal (enviamos producto al cliente)
                    quantity_delivered += qty
                    delivery_pickings.append(picking.name)
                    print(f"              → ENTREGA acumulada: {quantity_delivered}")

        # Calcular cantidad neta: lo que se entregó MENOS lo que se devolvió
        quantity_net = quantity_delivered - quantity_returned

        # Calcular total neto
        price_total_net = inv_line.price_unit * quantity_net

        # Detectar discrepancias
        discrepancy = abs(inv_line.quantity - quantity_net) > 0.01

        print(f"          RESUMEN:")
        print(f"            Facturado: {inv_line.quantity}")
        print(f"            Entregado: {quantity_delivered}")
        print(f"            Devuelto: {quantity_returned}")
        print(f"            Neto (Entregado - Devuelto): {quantity_net}")
        print(f"            Discrepancia: {discrepancy}")

        return {
            'invoice_id': invoice.id,
            'invoice_name': invoice.name,
            'invoice_date': invoice.invoice_date,
            'partner_id': invoice.partner_id.id,
            'product_id': inv_line.product_id.id if inv_line.product_id else False,
            'product_name': inv_line.name,
            'invoice_line_id': inv_line.id,
            'quantity_invoiced': inv_line.quantity,
            'quantity_delivered': quantity_delivered,
            'quantity_returned': quantity_returned,
            'quantity_net': quantity_net,
            'sale_order_ids': [(6, 0, sale_orders.ids)],
            'sale_order_names': ', '.join(sale_orders.mapped('name')) if sale_orders else '',
            'picking_ids': [(6, 0, pickings.ids)],
            'delivery_names': ', '.join(set(delivery_pickings)) if delivery_pickings else '',
            'return_names': ', '.join(set(return_pickings)) if return_pickings else '',
            'price_unit': inv_line.price_unit,
            'price_subtotal': inv_line.price_subtotal,
            'price_total_net': price_total_net,
            'has_returns': quantity_returned > 0,
            'discrepancy': discrepancy,
        }

    def action_export_excel(self):
        self.ensure_one()

        # Crear el archivo Excel en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Trazabilidad')

        # Estilos
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D3D3D3'
        })

        # Cabeceras
        headers = [
            'Factura', 'Fecha Factura', 'Estado Factura', 'Cliente',
            'Total Factura', 'Pedido', 'Estado Pedido', 'Albarán',
            'Tipo Albarán', 'Estado Albarán', 'Código Producto',
            'Nombre Producto', 'UdM', 'Cantidad'
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 15)  # Ancho de columna

        # Obtener datos
        domain = [
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]

        invoices = self.env['account.move'].search(domain)
        row = 1

        for invoice in invoices:
            # Obtener pedidos relacionados
            sale_orders = self.env['sale.order'].search([
                ('invoice_ids', 'in', invoice.ids)  # Nota: .ids en plural (lista de IDs)
            ])

            for order in sale_orders:
                # Obtener albaranes
                pickings = order.picking_ids

                for picking in pickings:
                    for move in picking.move_ids:
                        worksheet.write(row, 0, invoice.name)
                        worksheet.write(row, 1, invoice.invoice_date.strftime('%Y-%m-%d'))
                        worksheet.write(row, 2, invoice.state)
                        worksheet.write(row, 3, invoice.partner_id.name)
                        worksheet.write(row, 4, invoice.amount_total)
                        worksheet.write(row, 5, order.name)
                        worksheet.write(row, 6, order.state)
                        worksheet.write(row, 7, picking.name)
                        worksheet.write(row, 8, 'Devolución' if picking.is_return else 'Entrega')
                        worksheet.write(row, 9, picking.state)
                        worksheet.write(row, 10, move.product_id.default_code or '')
                        worksheet.write(row, 11, move.product_id.name)
                        worksheet.write(row, 12, move.product_uom.name)
                        row += 1

        workbook.close()

        # Crear adjunto
        excel_data = output.getvalue()
        filename = f'Trazabilidad_{self.date_from}_{self.date_to}.xlsx'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(excel_data),
            'store_fname': filename,
            'type': 'binary'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}/{filename}?download=true',
            'target': 'self',
        }
