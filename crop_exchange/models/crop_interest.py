# -*- coding: utf-8 -*-
from odoo import fields, models


class CropInterest(models.Model):
    """A buyer's interest request on a public listing.

    Submitted anonymously from the website (no login required). The
    buyer's contact details are visible only to platform admins - the
    provider is never contacted directly by the buyer. Admin staff
    review the request and manually connect the two parties
    (phone/WhatsApp, off-platform), then mark it 'linked'.
    """

    _name = "crop.interest"
    _description = "Buyer Interest Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "buyer_name"

    listing_id = fields.Many2one("crop.listing", required=True, tracking=True, ondelete="cascade")
    provider_id = fields.Many2one(
        "crop.provider", related="listing_id.provider_id", store=True, readonly=True
    )

    buyer_name = fields.Char(required=True)
    buyer_phone = fields.Char(required=True)
    buyer_email = fields.Char()
    message = fields.Text("Buyer Message")

    state = fields.Selection(
        [
            ("new", "New"),
            ("processing", "Admin Processing"),
            ("linked", "Linked / Connected"),
            ("rejected", "Rejected"),
        ],
        default="new",
        required=True,
        tracking=True,
    )
    admin_notes = fields.Text("Internal Admin Notes")

    def action_start_processing(self):
        self.write({"state": "processing"})

    def action_mark_linked(self):
        for rec in self:
            rec.state = "linked"
            rec.message_post(
                body="Buyer and provider have been connected by admin: %s"
                % (rec.admin_notes or "")
            )

    def action_reject(self):
        self.write({"state": "rejected"})
