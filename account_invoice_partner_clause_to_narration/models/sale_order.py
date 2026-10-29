from odoo import models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _prepare_invoice(self):
        self.ensure_one()
        vals = super(SaleOrder, self)._prepare_invoice()
        partner = self.partner_id
        invoice_clause = partner.invoice_clause

        if partner and invoice_clause and invoice_clause.used_for == "invoice":

            if vals.get("narration"):
                vals["narration"] += "{}{}".format("\n", invoice_clause.clause)
            else:
                vals["narration"] += "{}".format(invoice_clause.clause)

        return vals
