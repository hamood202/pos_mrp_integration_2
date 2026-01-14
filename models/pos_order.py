from odoo import models, api, fields, _
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to automatically generate Manufacturing Orders (MO)
        for products marked for POS manufacturing.
        """
        orders = super().create(vals_list)
        
        for order in orders:
            # 1. Filter order lines for products requiring POS manufacturing
            manufactured_lines = order.lines.filtered(
                lambda l: l.product_id.product_tmpl_id.pos_manufacture
            )

            # 2. Aggregate quantities by product
            products_to_process = {}
            for line in manufactured_lines:
                product = line.product_id
                products_to_process[product] = products_to_process.get(product, 0.0) + line.qty

            # 3. Process each product to create Manufacturing Orders
            for product, total_qty in products_to_process.items():
                # Find Bill of Materials (BoM) - Odoo 17 returns a defaultdict
                bom_data = self.env['mrp.bom']._bom_find(product, company_id=order.company_id.id)
                bom = bom_data.get(product) if isinstance(bom_data, dict) else bom_data

                if not bom:
                    raise UserError(
                        _("Cannot sell product '%s' via POS: No Bill of Materials found.") 
                        % product.display_name
                    )

                # 4. Raw Material Availability Check
                for bom_line in bom.bom_line_ids:
                    component = bom_line.product_id
                    # Calculate required quantity based on BoM ratio
                    required_qty = (bom_line.product_qty / bom.product_qty) * total_qty
                    
                    if component.qty_available < required_qty:
                        raise UserError(_(
                            "Insufficient stock for component '%(comp)s'. "
                            "Required for '%(prod)s': %(req).2f, Available: %(avail).2f"
                        ) % {
                            'comp': component.display_name,
                            'prod': product.display_name,
                            'req': required_qty,
                            'avail': component.qty_available
                        })

                # 5. Create the Manufacturing Order (MO)
                manufacturing_order = self.env['mrp.production'].sudo().create({
                    'product_id': product.id,
                    'product_qty': total_qty,
                    'product_uom_id': product.uom_id.id,
                    'bom_id': bom.id,
                    'origin': order.name or order.pos_reference,
                    'company_id': order.company_id.id,
                })
                
                # 6. Confirm the MO to reserve materials
                manufacturing_order.action_confirm()
                
                # Optional: Automatically mark as done (Uncomment if needed)
                # try:
                #     manufacturing_order.button_mark_done()
                # except Exception:
                #     pass

        return orders

    def open_related_mos(self):
        """
        Action for the Smart Button to display MOs linked to this POS Order.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Related Manufacturing Orders'),
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name)],
            'context': {'default_origin': self.name},
        }
