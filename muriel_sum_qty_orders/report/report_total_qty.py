# -*- coding: utf-8 -*-
from odoo import models


class ReportTotalQty(models.AbstractModel):
    _name = 'report.muriel_sum_qty_orders.report_total_qty_template'
    _description = 'Reporte suma cantidades pedidos'

    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids).exists()
        report_data = data or docs._prepare_total_qty_report_data()
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'data': report_data,
        }

