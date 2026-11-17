# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CropListing(models.Model):
    """A trader's public offer: a specific crop, quantity, price and
    location. The crop itself must come from the admin-curated
    crop.product master list - traders cannot invent new crops.
    """

    _name = "crop.listing"
    _description = "Crop Listing (Exchange Offer)"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(compute="_compute_name", store=True)
    provider_id = fields.Many2one(
        "crop.provider",
        required=True,
        tracking=True,
        domain=[("state", "=", "approved")],
        ondelete="cascade",
    )
    crop_id = fields.Many2one("crop.product", string="Crop", required=True, tracking=True)
    quantity = fields.Float(required=True)
    uom = fields.Selection(related="crop_id.default_uom", store=True, readonly=False)
    price_per_unit = fields.Monetary(required=True, tracking=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.ref("base.SDG", raise_if_not_found=False)
    )
    quality_grade = fields.Char("Quality / Specification")
    state_province = fields.Char("Wilaya / State", required=True)
    valid_until = fields.Date("Valid Until")

    state = fields.Selection(
        [
            ("available", "Available"),
            ("reserved", "Reserved"),
            ("expired", "Expired"),
        ],
        default="available",
        required=True,
        tracking=True,
    )

    interest_ids = fields.One2many("crop.interest", "listing_id", string="Interest Requests")
    interest_count = fields.Integer(compute="_compute_interest_count")

    @api.depends("crop_id", "quantity", "uom", "provider_id")
    def _compute_name(self):
        for rec in self:
            rec.name = "%s - %s %s (%s)" % (
                rec.crop_id.name or "?",
                rec.quantity,
                dict(rec._fields["uom"].selection).get(rec.uom, ""),
                rec.provider_id.name or "?",
            )

    @api.depends("interest_ids")
    def _compute_interest_count(self):
        for rec in self:
            rec.interest_count = len(rec.interest_ids)

    @api.constrains("provider_id")
    def _check_provider_approved(self):
        for rec in self:
            if rec.provider_id.state != "approved":
                raise ValidationError(
                    "Only approved providers may create crop listings."
                )

    def action_mark_reserved(self):
        self.write({"state": "reserved"})

    def action_mark_available(self):
        self.write({"state": "available"})

    @api.model
    def cron_expire_listings(self):
        """Scheduled action: flip listings past valid_until to expired."""
        expired = self.search(
            [("state", "=", "available"), ("valid_until", "<", fields.Date.today())]
        )
        expired.write({"state": "expired"})
