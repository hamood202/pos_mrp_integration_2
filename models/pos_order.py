from odoo import models, api, _
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            # التحقق من المنتجات التي تم تفعيل خيار التصنيع لها
            manufactured_lines = order.lines.filtered(
                lambda l: l.product_id.product_tmpl_id.pos_manufacture
            )

            products_to_manufacture = {}
            for line in manufactured_lines:
                product = line.product_id
                if product not in products_to_manufacture:
                    products_to_manufacture[product] = 0.0
                products_to_manufacture[product] += line.qty

            for product, total_qty in products_to_manufacture.items():
                # في Odoo 17، الدالة تعيد defaultdict، لذا يجب تمرير المنتج كأول وسيط
                bom_dict = self.env['mrp.bom']._bom_find(product, company_id=order.company_id.id)
                
                # استخراج سجل الـ BoM الفعلي من القاموس
                bom = bom_dict.get(product) if isinstance(bom_dict, dict) else bom_dict

                if not bom:
                    raise UserError(
                        _("Cannot sell product '%s' via POS: No Bill of Materials found.")
                        % product.display_name
                    )

                # التحقق من توفر المواد الخام قبل البدء
                for bom_line in bom.bom_line_ids:
                    component = bom_line.product_id
                    # حساب الكمية المطلوبة بناءً على كمية الـ BoM الأساسية
                    required_qty = (bom_line.product_qty / bom.product_qty) * total_qty
                    available_qty = component.qty_available

                    if available_qty < required_qty:
                        raise UserError(_(
                            "Cannot sell '%s'. Required component '%s' is insufficient. Required: %.2f, Available: %.2f"
                        ) % (
                            product.display_name,
                            component.display_name,
                            required_qty,
                            available_qty
                        ))

                # إنشاء أمر التصنيع (MO)
                mo = self.env['mrp.production'].sudo().create({
                    'product_id': product.id,
                    'product_qty': total_qty,
                    'product_uom_id': product.uom_id.id,
                    'bom_id': bom.id,
                    'origin': order.name or order.pos_reference or "POS Order",
                    'company_id': order.company_id.id,
                })
                
                # تأكيد الأمر (Confirm) لحجز المواد الخام
                mo.action_confirm()
                
                # إنهاء الأمر (Mark as Done) كما هو مطلوب في الكود الخاص بك
                # ملاحظة: button_mark_done في أودو 17 قد تحتاج لإنشاء سجلات الانتاج أولاً
                # # إذا واجهت مشكلة هنا، اكتفِ بـ action_confirm() ليقوم المخزني بإنهاء العمل يدوياً.
                # try:
                #     mo.button_mark_done()
                # except Exception:
                #     # في حال فشل الإغلاق التلقائي (بسبب قيود في النسخة)، يظل الأمر مؤكداً (Confirmed)
                #     pass

        return orders

    
    def open_related_mos(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Orders',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name)],
        }