# -*- coding: utf-8 -*-
from collections import defaultdict
from types import SimpleNamespace

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
        listings = Listing.search(
            [("state", "=", "available"), ("crop_id", "!=", False)]
        )

        totals = defaultdict(lambda: {"crop": False, "sum": 0.0, "count": 0})
        for listing in listings:
            bucket = totals[listing.crop_id.id]
            bucket["crop"] = listing.crop_id
            bucket["sum"] += listing.price_per_unit
            bucket["count"] += 1

        board_rows = [
            SimpleNamespace(
                crop=data["crop"],
                avg_price=data["sum"] / data["count"],
                avg_price_text="{:,.2f}".format(data["sum"] / data["count"]),
                offer_count=data["count"],
            )
            for data in totals.values()
            if data["count"]
        ]
        board_rows.sort(key=lambda r: r.crop.name or "")

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

    # ---------- Provider self-service: manage own crops & prices ----------
    # A provider's login only has the Provider/portal group, so they never
    # see the backend menus/views - they need a dedicated logged-in page
    # under /exchange to add and manage their own crop.listing records.
    def _get_current_provider(self):
        return request.env["crop.provider"].sudo().search(
            [("user_id", "=", request.env.user.id)], limit=1
        )

    @http.route(["/exchange/my"], type="http", auth="user", website=True)
    def my_listings(self, **kw):
        provider = self._get_current_provider()
        if not provider:
            return request.render("crop_exchange.my_listings_not_provider_template", {})
        if provider.state != "approved":
            return request.render(
                "crop_exchange.my_listings_pending_template", {"provider": provider}
            )
        crops = request.env["crop.product"].sudo().search([])
        states = request.env["res.country.state"].sudo().search([("country_id.code", "=", "SD")])
        return request.render(
            "crop_exchange.my_listings_template",
            {"provider": provider, "listings": provider.listing_ids, "crops": crops, "states": states},
        )

    @http.route(["/exchange/my/add"], type="http", auth="user", website=True, methods=["POST"], csrf=True)
    def my_listings_add(self, **post):
        provider = self._get_current_provider()
        if not provider or provider.state != "approved":
            return request.not_found()

        crop_id = int(post.get("crop_id") or 0)
        state_id = int(post.get("state_province") or 0)
        if not crop_id or not state_id or not post.get("price_per_unit"):
            return request.redirect("/exchange/my")

        request.env["crop.listing"].sudo().create(
            {
                "provider_id": provider.id,
                "crop_id": crop_id,
                "price_per_unit": float(post.get("price_per_unit")),
                "quantity": float(post.get("quantity") or 1.0),
                "quality_grade": post.get("quality_grade"),
                "state_province": state_id,
            }
        )
        return request.redirect("/exchange/my")

    @http.route(["/exchange/my/<int:listing_id>/toggle"], type="http", auth="user", website=True, methods=["POST"], csrf=True)
    def my_listings_toggle(self, listing_id, **post):
        provider = self._get_current_provider()
        listing = request.env["crop.listing"].sudo().browse(listing_id)
        if not provider or listing.provider_id.id != provider.id:
            return request.not_found()
        listing.state = "available" if listing.state == "reserved" else "reserved"
        return request.redirect("/exchange/my")

    @http.route(["/exchange/my/<int:listing_id>/delete"], type="http", auth="user", website=True, methods=["POST"], csrf=True)
    def my_listings_delete(self, listing_id, **post):
        provider = self._get_current_provider()
        listing = request.env["crop.listing"].sudo().browse(listing_id)
        if not provider or listing.provider_id.id != provider.id:
            return request.not_found()
        listing.unlink()
        return request.redirect("/exchange/my")
