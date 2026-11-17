# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class CropProvider(models.Model):
    """A trader / exporter that wants to list crops on the exchange.

    Mirrors the public onboarding form: registers in 'pending' state,
    an admin reviews and approves/rejects it. Only on approval does the
    provider get a portal user (group_provider) so they can log in and
    manage their own listings.
    """

    _name = "crop.provider"
    _description = "Crop Exchange Provider (Trader / Exporter)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char("Provider / Business Name", required=True, tracking=True)
    entity_type = fields.Selection(
        [
            ("company", "Registered Company / شركة مسجلة"),
            ("trade_name", "Trade Name / اسم تجاري"),
            ("freelancer", "Freelancer / فريلانسر"),
        ],
        required=True,
        default="company",
        tracking=True,
    )
    contact_name = fields.Char("Contact Person")
    phone = fields.Char(required=True, tracking=True)
    whatsapp = fields.Char("WhatsApp Number")
    email = fields.Char()
    state_province = fields.Char("Wilaya / State", required=True)
    country_id = fields.Many2one("res.country", default=lambda self: self.env.ref("base.sd", raise_if_not_found=False))
    years_experience = fields.Integer("Years of Experience")
    notes = fields.Text("Additional Notes")

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending",
        required=True,
        tracking=True,
    )
    rejection_reason = fields.Text()

    partner_id = fields.Many2one("res.partner", string="Related Partner", ondelete="restrict")
    user_id = fields.Many2one("res.users", string="Portal/Provider User", readonly=True)

    listing_ids = fields.One2many("crop.listing", "provider_id", string="Listings")
    listing_count = fields.Integer(compute="_compute_listing_count")

    @api.depends("listing_ids")
    def _compute_listing_count(self):
        for rec in self:
            rec.listing_count = len(rec.listing_ids)

    def action_approve(self):
        """Admin approval: create/activate the partner + provider user,
        add them to the Provider access group so they can log in and
        manage their own crop listings."""
        group_provider = self.env.ref("crop_exchange.group_crop_provider")
        for rec in self:
            if not rec.partner_id:
                rec.partner_id = self.env["res.partner"].create(
                    {
                        "name": rec.name,
                        "phone": rec.phone,
                        "mobile": rec.whatsapp,
                        "email": rec.email,
                        "is_company": rec.entity_type == "company",
                    }
                )
            if not rec.user_id:
                if not rec.email:
                    raise UserError(
                        "An email address is required before approving a provider "
                        "(needed to create their login)."
                    )
                user = self.env["res.users"].with_context(no_reset_password=True).create(
                    {
                        "name": rec.name,
                        "login": rec.email,
                        "email": rec.email,
                        "partner_id": rec.partner_id.id,
                        "groups_id": [(4, group_provider.id)],
                    }
                )
                rec.user_id = user.id
            else:
                rec.user_id.groups_id = [(4, group_provider.id)]
            rec.state = "approved"
            rec.message_post(body="Provider approved and portal access granted.")

    def action_reject(self):
        for rec in self:
            rec.state = "rejected"
            rec.message_post(body="Provider rejected: %s" % (rec.rejection_reason or "No reason given."))

    def action_reset_to_pending(self):
        self.write({"state": "pending"})
