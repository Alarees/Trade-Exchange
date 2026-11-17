# -*- coding: utf-8 -*-
{
    "name": "Crop Exchange Platform",
    "version": "20.0.1.0.0",
    "summary": "Crop/commodity exchange platform: provider onboarding, crop listings, public board, buyer interest requests mediated by admin.",
    "description": """
Trade Exchange — Crop/Commodity Exchange Platform
===================================================

A marketplace module where traders/exporters register as approved providers,
list crops from an admin-curated master list with quantity/price/location,
and the public can browse a free listing board. Interested buyers never get
provider contact info directly — they submit an interest request that is
routed to platform admins, who mediate the connection.

Flow:
  1. Provider registers (public form) -> pending
  2. Admin reviews -> approved / rejected
  3. Approved provider creates crop listings (crop limited to admin master list)
  4. Listings are shown on a public, no-login board with filters
  5. Any visitor can submit an "interest request" on a listing
  6. Admin reviews the request and connects buyer <-> provider manually
""",
    "author": "Trade Exchange",
    "website": "https://trade-exchange.sd",
    "category": "Website/Website",
    "license": "LGPL-3",
    "depends": ["base", "mail", "website", "portal"],
    "data": [
        "security/crop_exchange_security.xml",
        "security/ir.access.csv",
        "data/crop_exchange_data.xml",
        "views/crop_product_views.xml",
        "views/crop_interest_views.xml",
        "views/crop_listing_views.xml",
        "views/crop_provider_views.xml",
        "views/website_templates.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "crop_exchange/static/src/js/board_filters.js",
        ],
    },
    "installable": True,
    "application": True,
}
