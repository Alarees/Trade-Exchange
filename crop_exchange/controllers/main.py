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

    # ---------- Public exchange board: one row per crop, averaged ----------
    @http.route(["/exchange"], type="http", auth="public", website=True, sitemap=True)
    def exchange_board(self, **kw):
        Listing = request.env["crop.listing"].sudo()
        grouped = Listing.read_group(
            [("state", "=", "available")],
            ["crop_id"],
            ["price_per_unit:avg", "__count"],
        )
        board_rows = []
        for g in grouped:
            crop = request.env["crop.product"].sudo().browse(g["crop_id"][0]) if g["crop_id"] else False
            if not crop:
                continue
            board_rows.append(
                {
                    "crop": crop,
                    "avg_price": g["price_per_unit"],
                    "offer_count": g["__count"],
                }
            )
        board_rows.sort(key=lambda r: r["crop"].name or "")

        return request.render(
            "crop_exchange.exchange_board_template",
            {"board_rows": board_rows},
        )

    # ---------- Crop detail: every provider's price for this crop ----------
    @http.route(["/exchange/crop/<int:crop_id>"], type="http", auth="public", website=True)
    def exchange_crop_detail(self, crop_id, **kw):
        crop = request.env["crop.product"].sudo().browse(crop_id)
        if not crop.exists():
            return request.not_found()
        listings = request.env["crop.listing"].sudo().search(
            [("crop_id", "=", crop_id), ("state", "=", "available")],
            order="price_per_unit asc",
        )
        return request.render(
            "crop_exchange.exchange_crop_detail_template",
            {"crop": crop, "listings": listings},
        )

    # ---------- Single listing detail + interest form ----------
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
