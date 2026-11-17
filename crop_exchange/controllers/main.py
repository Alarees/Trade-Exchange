# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class CropExchangeController(http.Controller):
    """All routes here are public (no login) - every ORM call uses
    sudo() deliberately because the direct ACLs for the public group
    are intentionally closed (see ir.model.access.csv). Validation of
    what an anonymous visitor may write happens here in the
    controller, not via open model ACLs.
    """

    # ---------- Public exchange board ----------
    @http.route(["/exchange", "/exchange/page/<int:page>"], type="http", auth="public", website=True, sitemap=True)
    def exchange_board(self, page=1, crop_id=None, state_province=None, **kw):
        Listing = request.env["crop.listing"].sudo()
        domain = [("state", "=", "available")]
        if crop_id:
            domain.append(("crop_id", "=", int(crop_id)))
        if state_province:
            domain.append(("state_province", "ilike", state_province))

        listings = Listing.search(domain, order="create_date desc")
        crops = request.env["crop.product"].sudo().search([])

        return request.render(
            "crop_exchange.exchange_board_template",
            {
                "listings": listings,
                "crops": crops,
                "selected_crop_id": int(crop_id) if crop_id else None,
                "selected_state": state_province or "",
            },
        )

    @http.route(["/exchange/listing/<int:listing_id>"], type="http", auth="public", website=True)
    def exchange_listing_detail(self, listing_id, **kw):
        listing = request.env["crop.listing"].sudo().browse(listing_id)
        if not listing.exists() or listing.state != "available":
            return request.not_found()
        return request.render("crop_exchange.exchange_listing_detail_template", {"listing": listing})

    # ---------- Buyer interest request (public, no login) ----------
    @http.route(["/exchange/listing/<int:listing_id>/interest"], type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def submit_interest(self, listing_id, **post):
        listing = request.env["crop.listing"].sudo().browse(listing_id)
        if not listing.exists() or listing.state != "available":
            return request.not_found()

        buyer_name = (post.get("buyer_name") or "").strip()
        buyer_phone = (post.get("buyer_phone") or "").strip()
        if not buyer_name or not buyer_phone:
            return request.render(
                "crop_exchange.exchange_listing_detail_template",
                {"listing": listing, "error": "الاسم ورقم الهاتف مطلوبان."},
            )

        interest = request.env["crop.interest"].sudo().create(
            {
                "listing_id": listing.id,
                "buyer_name": buyer_name,
                "buyer_phone": buyer_phone,
                "buyer_email": post.get("buyer_email"),
                "message": post.get("message"),
            }
        )
        # Notify admins - activity on the admin group; SMS hook can be
        # wired to call the existing BrqSMS integration here.
        interest.activity_schedule(
            "mail.mail_activity_data_todo",
            summary="New buyer interest request on listing %s" % listing.name,
        )
        return request.render("crop_exchange.exchange_interest_thankyou_template", {"listing": listing})

    # ---------- Provider self-registration (public, no login) ----------
    @http.route(["/exchange/register"], type="http", auth="public", website=True)
    def provider_register_form(self, **kw):
        return request.render("crop_exchange.provider_register_template", {})

    @http.route(["/exchange/register/submit"], type="http", auth="public", website=True, methods=["POST"], csrf=True)
    def provider_register_submit(self, **post):
        required = ["name", "entity_type", "phone", "state_province"]
        missing = [f for f in required if not (post.get(f) or "").strip()]
        if missing:
            return request.render(
                "crop_exchange.provider_register_template",
                {"error": "الحقول التالية مطلوبة: %s" % ", ".join(missing), "post": post},
            )

        request.env["crop.provider"].sudo().create(
            {
                "name": post.get("name"),
                "entity_type": post.get("entity_type"),
                "contact_name": post.get("contact_name"),
                "phone": post.get("phone"),
                "whatsapp": post.get("whatsapp"),
                "email": post.get("email"),
                "state_province": post.get("state_province"),
                "years_experience": int(post.get("years_experience") or 0),
                "notes": post.get("notes"),
                "state": "pending",
            }
        )
        return request.render("crop_exchange.provider_register_thankyou_template", {})
