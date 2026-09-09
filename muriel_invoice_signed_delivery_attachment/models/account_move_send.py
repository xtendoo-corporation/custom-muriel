# -*- coding: utf-8 -*-
from odoo import api, models

DELIVERY_SLIP_REPORT = 'stock.report_deliveryslip'


class AccountMoveSend(models.AbstractModel):
    _inherit = 'account.move.send'

    @api.model
    def _get_mail_params(self, move, move_data):
        mail_params = super()._get_mail_params(move, move_data)

        pickings = move._get_signed_delivery_pickings()
        if pickings:
            report = self.env['ir.actions.report'].with_company(move.company_id)
            content, report_type = report._pre_render_qweb_pdf(DELIVERY_SLIP_REPORT, res_ids=pickings.ids)
            content_by_picking_id = report._get_splitted_report(DELIVERY_SLIP_REPORT, content, report_type)

            for picking in pickings:
                picking_content = content_by_picking_id.get(picking.id)
                if not picking_content:
                    continue
                filename = f"{picking.name.replace('/', '_')}.pdf"
                mail_params['attachments'].append((filename, picking_content))

        return mail_params
