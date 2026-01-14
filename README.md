# POS MRP Integration

Automatically create manufacturing orders when selling products via POS.


POS MRP Integration
Overview
This module bridges the gap between Point of Sale (POS) and Manufacturing (MRP) in Odoo 17. It enables automated production workflows triggered by retail sales, ensuring that any product sold via the POS—which requires assembly or manufacturing—instantly generates the corresponding production orders in the backend.

Key Features
Automatic MO Creation: Generates Manufacturing Orders (MO) immediately after a POS order is validated.

Inventory Guarding: Automatically checks for raw material availability before allowing a sale to proceed.

Real-time Traceability: Links POS receipts to Manufacturing Orders via the "Source Document" (Origin) field.

Smart Integration: Adds a "Smart Button" to the POS Order form view for quick access to related production records.

BOM Validation: Prevents the sale of manufactured goods if no Bill of Materials (BoM) is defined.