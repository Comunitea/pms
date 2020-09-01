# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsReservationLine(models.Model):
    _name = "pms.reservation.line"
    _description = "Reservations by day"
    _order = "date"

    # Default Methods ang Gets

    def name_get(self):
        result = []
        for res in self:
            date = fields.Date.from_string(res.date)
            name = u"{}/{}".format(date.day, date.month)
            result.append((res.id, name))
        return result

    # Fields declaration
    reservation_id = fields.Many2one(
        "pms.reservation",
        string="Reservation",
        ondelete="cascade",
        required=True,
        copy=False,
    )
    move_line_ids = fields.Many2many(
        "account.move.line",
        "reservation_line_move_rel",
        "reservation_line_id",
        "move_line_id",
        string="Invoice Lines",
        readonly=True,
        copy=False,
    )
    pms_property_id = fields.Many2one(
        "pms.property",
        store=True,
        readonly=True,
        related="reservation_id.pms_property_id",
    )
    date = fields.Date("Date")
    state = fields.Selection(related="reservation_id.state")
    price = fields.Float(
        string="Price",
        digits=("Product Price"),
        compute="_compute_price",
        store=True,
        readonly=False,
    )
    cancel_discount = fields.Float(
        string="Cancel Discount (%)",
        digits=("Discount"),
        default=0.0,
        compute="_compute_cancel_discount",
        store=True,
        readonly=False,
    )
    discount = fields.Float(string="Discount (%)", digits=("Discount"), default=0.0)

    # Compute and Search methods
    @api.depends(
        "date",
        "reservation_id.pricelist_id",
        "reservation_id.room_type_id",
        "reservation_id.reservation_type",
    )
    def _compute_price(self):
        for line in self:
            reservation = line.reservation_id
            room_type_id = reservation.room_type_id.id
            product = self.env["pms.room.type"].browse(room_type_id).product_id
            partner = self.env["res.partner"].browse(reservation.partner_id.id)
            product = product.with_context(
                lang=partner.lang,
                partner=partner.id,
                quantity=1,
                date=line.date,
                pricelist=reservation.pricelist_id.id,
                uom=product.uom_id.id,
            )
            line.price = self.env["account.tax"]._fix_tax_included_price_company(
                line._get_display_price(product),
                product.taxes_id,
                line.reservation_id.tax_ids,
                line.reservation_id.company_id,
            )
            # TODO: Out of service 0 amount

    # TODO: Refact method and allowed cancelled single days
    @api.depends("reservation_id.cancelled_reason")
    def _compute_cancel_discount(self):
        for line in self:
            line.cancel_discount = 0
            # reservation = line.reservation_id
            # pricelist = reservation.pricelist_id
            # if reservation.state == "cancelled":
            #     # TODO: Set 0 qty on cancel room services change to compute day_qty
            #     # (view constrain service_line_days)
            #     for service in reservation.service_ids:
            #         service.service_line_ids.write({"day_qty": 0})
            #         service._compute_days_qty()
            #     if (
            #         reservation.cancelled_reason
            #         and pricelist
            #         and pricelist.cancelation_rule_id
            #     ):
            #         date_start_dt = fields.Date.from_string(
            #             reservation.real_checkin or reservation.checkin
            #         )
            #         date_end_dt = fields.Date.from_string(
            #             reservation.real_checkout or reservation.checkout
            #         )
            #         days = abs((date_end_dt - date_start_dt).days)
            #         rule = pricelist.cancelation_rule_id
            #         if reservation.cancelled_reason == "late":
            #             discount = 100 - rule.penalty_late
            #             if rule.apply_on_late == "first":
            #                 days = 1
            #             elif rule.apply_on_late == "days":
            #                 days = rule.days_late
            #         elif reservation.cancelled_reason == "noshow":
            #             discount = 100 - rule.penalty_noshow
            #             if rule.apply_on_noshow == "first":
            #                 days = 1
            #             elif rule.apply_on_noshow == "days":
            #                 days = rule.days_late - 1
            #         elif reservation.cancelled_reason == "intime":
            #             discount = 100

            #         checkin = reservation.real_checkin or reservation.checkin
            #         dates = []
            #         for i in range(0, days):
            #             dates.append(
            #                 (
            #                     fields.Date.from_string(checkin) + timedelta(days=i)
            #                 ).strftime(DEFAULT_SERVER_DATE_FORMAT)
            #             )
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date in dates
            #         ).update({"cancel_discount": discount})
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date not in dates
            #         ).update({"cancel_discount": 100})
            #     else:
            #         reservation.reservation_line_ids.update({"cancel_discount": 0})
            # else:
            #     reservation.reservation_line_ids.update({"cancel_discount": 0})

    # Constraints and onchanges
    @api.constrains("date")
    def constrains_duplicated_date(self):
        for record in self:
            duplicated = record.reservation_id.reservation_line_ids.filtered(
                lambda r: r.date == record.date and r.id != record.id
            )
            if duplicated:
                raise ValidationError(_("Duplicated reservation line date"))

    @api.constrains("state")
    def constrains_service_cancel(self):
        for record in self:
            if record.state == "cancelled":
                room_services = record.reservation_id.service_ids
                for service in room_services:
                    cancel_lines = service.service_line_ids.filtered(
                        lambda r: r.date == record.date
                    )
                    cancel_lines.day_qty = 0

    def _get_display_price(self, product):
        if self.reservation_id.pricelist_id.discount_policy == "with_discount":
            return product.with_context(
                pricelist=self.reservation_id.pricelist_id.id
            ).price
        product_context = dict(
            self.env.context,
            partner_id=self.reservation_id.partner_id.id,
            date=self.date,
            uom=product.uom_id.id,
        )

        final_price, rule_id = self.reservation_id.pricelist_id.with_context(
            product_context
        ).get_product_price_rule(product, 1.0, self.reservation_id.partner_id)
        base_price, currency = self.with_context(
            product_context
        )._get_real_price_currency(
            product, rule_id, 1, product.uom_id, self.reservation_id.pricelist_id.id
        )
        if currency != self.reservation_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price,
                self.reservation_id.pricelist_id.currency_id,
                self.reservation_id.company_id or self.env.company,
                fields.Date.today(),
            )
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)
