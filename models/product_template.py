from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pos_manufacture = fields.Boolean(
        string="Manufacture in POS",
        help="If enabled, selling this product via POS will auto-create a Manufacturing Order."
    )

    @api.constrains('pos_manufacture')
    def _check_bom_exists(self):
        """
        Validates that a Bill of Materials (BoM) exists for products marked for POS manufacturing.
        
        This constraint ensures data integrity by preventing the user from enabling 
        the 'Manufacture in POS' feature if the product cannot actually be produced 
        due to a missing BoM.
        
        :raises ValidationError: If 'pos_manufacture' is True but no BoM is linked 
                                 to the product template or its variants.
        """
        for template in self:
            if template.pos_manufacture:
                # Search for any BoM linked to this template or its specific variants
                bom_count = self.env['mrp.bom'].search_count([
                    '|', 
                    ('product_tmpl_id', '=', template.id),
                    ('product_id.product_tmpl_id', '=', template.id)
                ])
                
                if not bom_count:
                    raise ValidationError(_(
                        "Product '%s' has 'Manufacture in POS' enabled, but no Bill of Materials (BoM) "
                        "was found. Please define a BoM before enabling this feature."
                    ) % template.name)
