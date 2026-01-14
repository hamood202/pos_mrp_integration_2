{
    "name": "POS MRP Integration 2",
    "version": "1.0",
    "category": "Point of Sale",
    "summary": "Auto-create MO when selling manufacturing products via POS",
    "depends": ["point_of_sale", "mrp", "stock"],
    "data": [
        "views/product_template_views.xml",
        "views/pos_order_views.xml"
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3"
}