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
                print(f"          Picking {picking.name} : {picking.state} (no procesado)")
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
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })

        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'num_format': '#,##0.00'
        })

        invoice_header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E7E6E6',
            'border': 1
        })

        normal_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0.00'
        })

        text_format = workbook.add_format({
            'border': 1
        })

        # Cabeceras - IGUAL QUE LA VISTA LISTA
        headers = [
            'Fecha',
            'Factura',
            'Cliente',
            'Producto',
            'Descripción',
            'Pedidos',
            'Entregas',
            'Devoluciones',
            'Cantidad Enviada',
            'Cantidad Devuelta',
            'Total Facturado',
            'Subtotal Facturado',
        ]

        # Escribir cabeceras
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Ajustar anchos de columna
        worksheet.set_column(0, 0, 12)  # Fecha
        worksheet.set_column(1, 1, 18)  # Factura
        worksheet.set_column(2, 2, 25)  # Cliente
        worksheet.set_column(3, 3, 15)  # Producto
        worksheet.set_column(4, 4, 30)  # Descripción
        worksheet.set_column(5, 5, 20)  # Pedidos
        worksheet.set_column(6, 6, 20)  # Entregas
        worksheet.set_column(7, 7, 20)  # Devoluciones
        worksheet.set_column(8, 11, 15)  # Cantidades y totales

        # Obtener datos usando el mismo método que la vista
        domain = [
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]

        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        invoices = self.env['account.move'].search(domain, order='invoice_date desc, name')

        row = 1
        grand_total_sent = 0
        grand_total_returned = 0
        grand_total_invoiced = 0
        grand_total_amount = 0

        # Procesar cada factura (AGRUPADO POR FACTURA)
        for invoice in invoices:
            invoice_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')

            if self.product_ids:
                invoice_lines = invoice_lines.filtered(lambda l: l.product_id in self.product_ids)

            if not invoice_lines:
                continue

            # Cabecera de factura
            worksheet.write(row, 0, invoice.invoice_date.strftime('%d/%m/%Y'), invoice_header_format)
            worksheet.write(row, 1, invoice.name, invoice_header_format)
            worksheet.write(row, 2, invoice.partner_id.name, invoice_header_format)
            worksheet.write(row, 3, '', invoice_header_format)
            worksheet.write(row, 4, '', invoice_header_format)
            worksheet.write(row, 5, '', invoice_header_format)
            worksheet.write(row, 6, '', invoice_header_format)
            worksheet.write(row, 7, '', invoice_header_format)
            worksheet.write(row, 8, '', invoice_header_format)
            worksheet.write(row, 9, '', invoice_header_format)
            worksheet.write(row, 10, '', invoice_header_format)
            worksheet.write(row, 11, '', invoice_header_format)
            row += 1

            # Totales por factura
            invoice_total_sent = 0
            invoice_total_returned = 0
            invoice_total_invoiced = 0
            invoice_total_amount = 0

            # Líneas de la factura
            for inv_line in invoice_lines:
                trace_data = self._compute_trace_line_data(invoice, inv_line)

                worksheet.write(row, 0, '', text_format)
                worksheet.write(row, 1, '', text_format)
                worksheet.write(row, 2, '', text_format)
                worksheet.write(row, 3, trace_data['product_id'] and self.env['product.product'].browse(
                    trace_data['product_id']).default_code or '', text_format)
                worksheet.write(row, 4, trace_data['product_name'], text_format)
                worksheet.write(row, 5, trace_data['sale_order_names'], text_format)
                worksheet.write(row, 6, trace_data['delivery_names'], text_format)
                worksheet.write(row, 7, trace_data['return_names'], text_format)
                worksheet.write(row, 8, trace_data['quantity_delivered'], normal_format)
                worksheet.write(row, 9, trace_data['quantity_returned'], normal_format)
                worksheet.write(row, 10, trace_data['quantity_invoiced'], normal_format)
                worksheet.write(row, 11, trace_data['price_subtotal'], normal_format)
                worksheet.write(row, 12, '', text_format)

                invoice_total_sent += trace_data['quantity_delivered']
                invoice_total_returned += trace_data['quantity_returned']
                invoice_total_invoiced += trace_data['quantity_invoiced']
                invoice_total_amount += trace_data['price_subtotal']

                row += 1

            # Subtotales por factura
            worksheet.write(row, 0, '', total_format)
            worksheet.write(row, 1, '', total_format)
            worksheet.write(row, 2, '', total_format)
            worksheet.write(row, 3, '', total_format)
            worksheet.write(row, 4, 'SUBTOTAL FACTURA', total_format)
            worksheet.write(row, 5, '', total_format)
            worksheet.write(row, 6, '', total_format)
            worksheet.write(row, 7, '', total_format)
            worksheet.write(row, 8, invoice_total_sent, total_format)
            worksheet.write(row, 9, invoice_total_returned, total_format)
            worksheet.write(row, 10, invoice_total_invoiced, total_format)
            worksheet.write(row, 11, invoice_total_amount, total_format)
            worksheet.write(row, 12, '', total_format)
            row += 1

            # Línea en blanco entre facturas
            row += 1

            # Acumular totales generales
            grand_total_sent += invoice_total_sent
            grand_total_returned += invoice_total_returned
            grand_total_invoiced += invoice_total_invoiced
            grand_total_amount += invoice_total_amount

        # TOTALES GENERALES
        grand_total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 2,
            'num_format': '#,##0.00'
        })

        worksheet.write(row, 0, '', grand_total_format)
        worksheet.write(row, 1, '', grand_total_format)
        worksheet.write(row, 2, '', grand_total_format)
        worksheet.write(row, 3, '', grand_total_format)
        worksheet.write(row, 4, 'TOTAL GENERAL', grand_total_format)
        worksheet.write(row, 5, '', grand_total_format)
        worksheet.write(row, 6, '', grand_total_format)
        worksheet.write(row, 7, '', grand_total_format)
        worksheet.write(row, 8, grand_total_sent, grand_total_format)
        worksheet.write(row, 9, grand_total_returned, grand_total_format)
        worksheet.write(row, 10, grand_total_invoiced, grand_total_format)
        worksheet.write(row, 11, grand_total_amount, grand_total_format)
        worksheet.write(row, 12, '', grand_total_format)

        # Congelar primera fila
        worksheet.freeze_panes(1, 0)

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
