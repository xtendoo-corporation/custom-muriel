from odoo import models, fields, api
from datetime import datetime
import xlsxwriter
import base64
import io


class InvoiceSaleDeliveryTraceWizard(models.TransientModel):
    _name = 'invoice.sale.delivery.trace.wizard'
    _description = 'Asistente de Trazabilidad Facturas-Ventas-Entregas'

    date_from = fields.Date(
        string='Fecha Desde',
        required=True,
        default=fields.Date.context_today
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True,
        default=fields.Date.context_today
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    def action_generate_trace(self):
        self.ensure_one()
        domain = [
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]

        invoices = self.env['account.move'].search(domain)
        if not invoices:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No se encontraron facturas en el rango de fechas seleccionado.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        action = {
            'name': 'Trazabilidad Facturas-Ventas-Entregas',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'create': False},
            'target': 'current',
        }
        return action

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
