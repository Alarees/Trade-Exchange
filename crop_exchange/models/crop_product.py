# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CropProduct(models.Model):
    """Admin-curated master list of crops available on the exchange.

    Traders/exporters can only create listings for crops that already
    exist in this list - they cannot add a new crop on their own.
    """

    _name = "crop.product"
    _description = "Crop Master (Exchange Catalog)"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    category = fields.Selection(
        [
            ("cereal", "Cereals / الحبوب"),
            ("oilseed", "Oilseeds / البذور الزيتية"),
            ("legume", "Legumes / البقوليات"),
            ("fruit_veg", "Fruits & Vegetables / فواكه وخضروات"),
            ("spice", "Spices / توابل"),
            ("livestock", "Livestock & Animal Products / ثروة حيوانية"),
            ("other", "Other / أخرى"),
        ],
        default="cereal",
        required=True,
    )
    default_uom = fields.Selection(
        [
            ("ton", "Ton / طن"),
            ("kg", "Kilogram / كيلوجرام"),
            ("sack50", "50kg Sack / جوال 50 كجم"),
            ("head", "Head (livestock) / رأس"),
        ],
        default="ton",
        required=True,
    )
    image_1920 = fields.Image(max_width=1024, max_height=1024)
    active = fields.Boolean(default=True)
    listing_ids = fields.One2many("crop.listing", "crop_id", string="Listings")
    listing_count = fields.Integer(compute="_compute_listing_count")

    @api.depends("listing_ids")
    def _compute_listing_count(self):
        for rec in self:
            rec.listing_count = len(rec.listing_ids)
