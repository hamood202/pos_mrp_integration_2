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
        for template in self:
            if template.pos_manufacture:
                has_bom = self.env['mrp.bom'].search([
                    '|', ('product_tmpl_id', '=', template.id),
                    ('product_id.product_tmpl_id', '=', template.id)
                ], limit=1)
                if not has_bom:
                    raise ValidationError(_(
                        "Product '%s' has 'Manufacture in POS' enabled but no BoM found!"
                    ) % template.name)