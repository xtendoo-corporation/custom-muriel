import base64
import io
from datetime import datetime
import xlsxwriter

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class InvoiceSaleDeliveryTraceWizard(models.TransientModel):
    _name = 'invoice.sale.delivery.trace.wizard'
    _description = 'Asistente de Trazabilidad Facturas-Ventas-Entregas'

    date_from = fields.Date(
        string='Fecha Desde',
        required=True
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )

    def action_generate_trace(self):
        self.ensure_one()
        domain = [
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id)
        ]

        invoices = self.env['account.move'].search(domain)
        if not invoices:
            raise ValidationError(_('No se encontraron facturas en el rango de fechas seleccionado.'))

        return self._show_trace_results(invoices)

    def action_export_excel(self):
        self.ensure_one()
        domain = [
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id)
        ]

        invoices = self.env['account.move'].search(domain)
        if not invoices:
            raise ValidationError(_('No se encontraron facturas en el rango de fechas seleccionado.'))

        return self._generate_excel_report(invoices)

    def _show_trace_results(self, invoices):
        return {
            'name': _('Resultados de Trazabilidad'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {
                'create': False,
                'search_default_posted': 1,
            },
            'target': 'current',
        }

    def _generate_excel_report(self, invoices):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Traceability')

        # Formatos
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
            'Tipo Operación', 'Estado Albarán', 'Código Producto',
            'Nombre Producto', 'UdM', 'Cantidad'
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 15)

        row = 1
        for invoice in invoices:
            sign = -1 if invoice.move_type == 'out_refund' else 1

            for sale_order in invoice.related_sale_order_ids:
                for picking in sale_order.related_picking_ids:
                    for move in picking.move_ids_without_package:
                        worksheet.write(row, 0, invoice.name)
                        worksheet.write(row, 1, invoice.invoice_date.strftime('%Y-%m-%d'))
                        worksheet.write(row, 2, dict(invoice._fields['state'].selection).get(invoice.state))
                        worksheet.write(row, 3, invoice.partner_id.name)
                        worksheet.write(row, 4, invoice.amount_total * sign)
                        worksheet.write(row, 5, sale_order.name)
                        worksheet.write(row, 6, dict(sale_order._fields['state'].selection).get(sale_order.state))
                        worksheet.write(row, 7, picking.name)
                        worksheet.write(row, 8, picking.picking_type_label)
                        worksheet.write(row, 9, dict(picking._fields['state'].selection).get(picking.state))
                        worksheet.write(row, 10, move.product_id.default_code or '')
                        worksheet.write(row, 11, move.product_id.name)
                        worksheet.write(row, 12, move.product_uom.name)
                        worksheet.write(row, 13, move.quantity_done)
                        row += 1

        workbook.close()
        output.seek(0)

        # Crear adjunto
        xlsx_data = output.getvalue()
        attachment = self.env['ir.attachment'].create({
            'name': f'Trazabilidad_{self.date_from}_{self.date_to}.xlsx',
            'datas': base64.b64encode(xlsx_data),
            'type': 'binary',
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
