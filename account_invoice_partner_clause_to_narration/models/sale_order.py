from odoo import models
from odoo.tools.mail import append_content_to_html, is_html_empty, plaintext2html


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _prepare_invoice(self):
        self.ensure_one()
        vals = super()._prepare_invoice()
        vals["narration"] = self._narration_with_partner_invoice_clause(
            vals.get("narration"), self.partner_id
        )
        return vals

    def _narration_with_partner_invoice_clause(self, narration, partner):
        clause = partner.invoice_clause
        if not clause or clause.used_for != "invoice" or not clause.clause:
            return narration
        clause_html = plaintext2html(clause.clause)
        if is_html_empty(narration):
            return clause_html
        narration_html = str(narration)
        if str(clause_html) in narration_html:
            return narration
        return append_content_to_html(narration_html, clause.clause)
