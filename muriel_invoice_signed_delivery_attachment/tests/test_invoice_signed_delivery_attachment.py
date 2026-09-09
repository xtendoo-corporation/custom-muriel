# -*- coding: utf-8 -*-
import base64

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase

# 1x1 transparent PNG, used as a fake customer signature.
ONE_PIXEL_PNG = base64.b64encode(base64.b64decode(
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
))


@tagged('post_install', '-at_install')
class TestInvoiceSignedDeliveryAttachment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente de Prueba',
            'email': 'cliente@example.com',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Producto de Prueba',
            'type': 'consu',
            'is_storable': True,
            'invoice_policy': 'order',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2,
            })],
        })
        cls.sale_order.action_confirm()

        cls.picking = cls.sale_order.picking_ids
        for move in cls.picking.move_ids:
            move.quantity = move.product_uom_qty
        cls.picking.button_validate()
        cls.picking.signature = ONE_PIXEL_PNG

        cls.invoice = cls.sale_order._create_invoices()
        cls.invoice.action_post()

    def test_signed_picking_is_related(self):
        pickings = self.invoice._get_signed_delivery_pickings()
        self.assertEqual(pickings, self.picking)

    def test_unsigned_picking_is_not_related(self):
        self.picking.signature = False
        pickings = self.invoice._get_signed_delivery_pickings()
        self.assertFalse(pickings)

    def test_non_customer_invoice_has_no_related_pickings(self):
        vendor_bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
        })
        self.assertFalse(vendor_bill._get_signed_delivery_pickings())

    def test_mail_params_include_delivery_slip_attachment(self):
        account_move_send = self.env['account.move.send']
        move = self.invoice.sudo()
        moves_data = {move: account_move_send._get_default_sending_settings(move)}
        account_move_send._generate_invoice_documents(moves_data)

        mail_params = account_move_send._get_mail_params(move, moves_data[move])

        expected_filename = f"{self.picking.name.replace('/', '_')}.pdf"
        attachment_names = [name for name, _content in mail_params['attachments']]
        self.assertIn(expected_filename, attachment_names)

        picking_attachment = next(
            content for name, content in mail_params['attachments']
            if name == expected_filename
        )
        # In test mode, report rendering falls back to HTML instead of calling
        # wkhtmltopdf, so we only assert that content was actually generated.
        self.assertTrue(picking_attachment)

    def test_sending_invoice_by_email_attaches_signed_delivery(self):
        self.env['account.move.send']._generate_and_send_invoices(self.invoice, sending_methods={'email'})

        expected_filename = f"{self.picking.name.replace('/', '_')}.pdf"
        attachment_names = self.invoice.message_ids.attachment_ids.mapped('name')
        self.assertIn(expected_filename, attachment_names)

    def test_multiple_signed_deliveries_are_all_attached(self):
        """A single invoice can gather several signed deliveries (e.g. a partial
        delivery followed by its backorder) and all of them must be attached."""
        product = self.env['product.product'].create({
            'name': 'Producto Multi-Entrega',
            'type': 'consu',
            'is_storable': True,
            'invoice_policy': 'order',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 4,
            })],
        })
        sale_order.action_confirm()

        first_picking = sale_order.picking_ids
        first_picking.picking_type_id.create_backorder = 'ask'
        first_picking.move_ids.quantity = 2
        validate_result = first_picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(validate_result['context'])
        ).save()
        backorder_wizard.process()

        second_picking = sale_order.picking_ids - first_picking
        second_picking.move_ids.quantity = 2
        second_picking.button_validate()

        first_picking.signature = ONE_PIXEL_PNG
        second_picking.signature = ONE_PIXEL_PNG

        invoice = sale_order._create_invoices()
        invoice.action_post()

        pickings = invoice._get_signed_delivery_pickings()
        self.assertEqual(pickings, first_picking | second_picking)

        self.env['account.move.send']._generate_and_send_invoices(invoice, sending_methods={'email'})

        attachment_names = invoice.message_ids.attachment_ids.mapped('name')
        self.assertIn(f"{first_picking.name.replace('/', '_')}.pdf", attachment_names)
        self.assertIn(f"{second_picking.name.replace('/', '_')}.pdf", attachment_names)
