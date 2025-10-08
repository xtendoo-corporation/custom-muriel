# Trazabilidad Facturas-Ventas-Entregas (Muriel)

Este módulo proporciona trazabilidad completa entre facturas de cliente, pedidos de venta y entregas/devoluciones, con exportación a Excel.

## Características

- Trazabilidad completa entre Facturas → Pedidos → Entregas/Devoluciones
- Wizard con rango de fechas para consulta
- Exportación a Excel (.xlsx)
- Botón inteligente en facturas para ver pedidos relacionados
- Pestaña de entregas/devoluciones en pedidos de venta
- Compatible multi-empresa

## Instalación

1. Copiar el módulo a la carpeta custom-muriel
2. Instalar dependencia Python: `pip install xlsxwriter`
3. Actualizar lista de módulos en Odoo
4. Instalar el módulo "muriel_sale_invoice_delivery_trace"

## Uso

### Generar Informe de Trazabilidad

1. Ir a Ventas → Informes → Trazabilidad Facturas-Ventas-Entregas
2. O ir a Contabilidad → Informes → Trazabilidad Facturas-Ventas-Entregas
3. Seleccionar rango de fechas
4. Clic en "Ver Resultados" o "Exportar a Excel"

### Navegación desde Facturas

1. Abrir una factura de cliente
2. Usar el botón inteligente "Pedidos" para ver pedidos relacionados
3. En cada pedido, acceder a la pestaña "Entregas y Devoluciones"

### Formato Excel

El archivo Excel generado incluye:
- Datos de factura: número, fecha, estado, cliente, total
- Datos de pedido: número, estado
- Datos de albarán: número, tipo (Entrega/Devolución), estado
- Datos de producto: código, nombre, UdM, cantidad entregada

## Soporte

Para soporte contactar con el equipo de desarrollo.
