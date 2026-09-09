# Adjuntar Albaranes Firmados a Factura (Muriel)

Adjunta automáticamente al email de la factura todos los albaranes de entrega
relacionados que hayan sido firmados por el cliente.

## Funcionamiento

Al enviar una factura de cliente por correo (botón "Enviar", asistente de
Enviar e Imprimir, envío masivo o el cron de envío automático de facturas),
el módulo:

1. Localiza los pedidos de venta relacionados con la factura (a través de
   las líneas de factura o, si no las hay, del campo "Origen").
2. De esos pedidos, obtiene los albaranes de salida (`picking_type_id.code
   == 'outgoing'`) que estén validados (`state == 'done'`) y tengan firma
   del cliente (`signature`).
3. Genera el informe de albarán (`stock.report_deliveryslip`) de cada uno y
   lo adjunta al mismo correo de la factura.

No se adjunta nada si la factura no tiene albaranes firmados asociados.

## Dependencias

- `account`
- `sale_stock`
