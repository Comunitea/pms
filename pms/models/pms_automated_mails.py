from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PmsAutomatedMails(models.Model):
    _name = "pms.automated.mails"
    _description = "Automatic Mails"

    name = fields.Char(string="Name")

    pms_property_id = fields.Many2one(string="Property", comodel_name="pms.property")

    automated_actions_id = fields.Many2one(
        string="Automated Actions", comodel_name="base.automation", ondelete="cascade"
    )

    time = fields.Integer(string="Time")

    time_type = fields.Selection(
        string="Time Range",
        selection=[
            ("minutes", "Minutes"),
            ("hour", "Hour"),
            ("day", "Days"),
            ("month", "Months"),
        ],
        default="day",
    )
    template_id = fields.Many2one(
        string="Template", comodel_name="mail.template", required=True
    )

    model_id = fields.Many2one(
        string="Model", comodel_name="ir.model", compute="_compute_model_id", store=True
    )

    action = fields.Selection(
        string="Action",
        selection=[
            ("creation", "Reservation creation"),
            ("write", "Reservation modification"),
            ("cancel", "Reservation cancellation"),
            ("checkin", "Checkin"),
            ("checkout", "Checkout"),
            ("payment", "Payment"),
            ("invoice", "Invoice"),
        ],
        default="creation",
        required=True,
    )

    trigger = fields.Char(
        string="Trigger",
    )

    moment = fields.Selection(
        string="Moment",
        selection=[
            ("before", "Before"),
            ("after", "After"),
            ("in_act", "In the act"),
        ],
        default="before",
    )

    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals):
        name = vals.get("name")
        action = vals.get("action")
        time = vals.get("time")
        date_range_type = vals.get("time_type")
        template_id = vals.get("template_id")
        active = vals.get("active")
        moment = vals.get("moment")
        model_id = False
        model_field = False
        if action in ("creation", "write", "cancel"):
            if moment == "before":
                raise UserError(_("The moment for this action cannot be 'Before'"))
        if action in ("creation", "write", "cancel", "checkin", "checkout"):
            model_id = self.env["ir.model"].search([("name", "=", "Reservation")])
        elif action == "payment":
            model_id = self.env["ir.model"].search([("name", "=", "Payments")])
        action_server_vals = {
            "name": name,
            "state": "email",
            "usage": "ir_cron",
            "model_id": model_id.id,
        }
        action_server = self.env["ir.actions.server"].create(action_server_vals)
        dict_val = self._prepare_creation_write(action, time, moment)
        if not model_field:
            automated_actions_vals = {
                "active": active,
                "action_server_id": action_server.id,
                "trigger": dict_val["trigger"],
                "filter_domain": dict_val["filter_domain"],
                "trg_date_range": dict_val["time"],
                "trg_date_range_type": date_range_type,
                "template_id": template_id,
            }
        else:
            automated_actions_vals = {
                "active": active,
                "action_server_id": action_server.id,
                "trigger": dict_val["trigger"],
                "trg_date_id": dict_val["model_field"].id,
                "filter_domain": dict_val["filter_domain"],
                "trg_date_range": dict_val["time"],
                "trg_date_range_type": date_range_type,
                "template_id": template_id,
            }
        automated_action = self.env["base.automation"].create(automated_actions_vals)
        self.automated_actions_id = automated_action.id
        return super(PmsAutomatedMails, self).create(vals)

    def _prepare_creation_write(self, action, time, moment):
        trigger = False
        model_field = False
        filter_domain = False
        # action: create reservation
        if action == "creation":
            if moment == "in_act":
                trigger = "on_create"
            else:
                trigger = "on_time"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "date_order")]
                )

        # action: write and cancel reservation
        if action == "write" or action == "cancel":
            if action == "cancel":
                filter_domain = [("state", "=", "cancelled")]
            if moment == "in_act":
                trigger = "on_write"
            else:
                trigger = "on_time"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "write_date")]
                )

        # action: checkin
        if action == "checkin":
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "checkin")]
            )
            if moment == "in_act":
                filter_domain = [("checkin", "=", fields.Date.today())]
            elif moment == "before":
                time = time * (-1)

            # action: checkout
            if action == "checkout":
                trigger = "on_time"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "checkout")]
                )
                if moment == "in_act":
                    filter_domain = [("checkout", "=", fields.Date.today())]
                elif moment == "before":
                    time = time * (-1)
        result = {
            "trigger": trigger,
            "model_field": model_field,
            "filter_domain": filter_domain,
            "time": time,
        }
        return result
