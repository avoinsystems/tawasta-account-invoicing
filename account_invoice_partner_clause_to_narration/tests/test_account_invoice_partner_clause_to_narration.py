from odoo.tests import TransactionCase
from odoo.tools.mail import plaintext2html


class TestAccountInvoicePartnerClauseToNarration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_clause_obj = cls.env["partner.clause"]
        cls.res_partner_obj = cls.env["res.partner"]
        cls.sale_order_obj = cls.env["sale.order"]
        cls.product = cls.env["product.product"].create(
            {
                "name": "Example service",
                "type": "service",
                "invoice_policy": "order",
                "list_price": 10.0,
            }
        )
        cls.invoice_clause = cls.partner_clause_obj.create(
            {
                "name": "Standard invoice clause",
                "clause": "These products are of EU preferential origin.",
                "used_for": "invoice",
            }
        )
        cls.partner = cls.res_partner_obj.create(
            {
                "name": "Example Corp",
                "invoice_clause": cls.invoice_clause.id,
            }
        )
        cls.plain_partner = cls.res_partner_obj.create({"name": "Acme Ltd"})

    def _invoice_from_order(self, partner, note=None):
        vals = {
            "partner_id": partner.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "product_uom_qty": 1.0,
                    },
                )
            ],
        }
        if note is not None:
            vals["note"] = note
        order = self.sale_order_obj.create(vals)
        order.action_confirm()
        return order._create_invoices()

    def test_invoice_clause_is_added_to_the_invoice_narration(self):
        param_obj = self.env["ir.config_parameter"].sudo()
        param_obj.set_param("account.use_invoice_terms", False)

        invoice = self._invoice_from_order(self.partner)
        self.assertIn(
            "These products are of EU preferential origin.",
            invoice.narration,
        )

        noted = self._invoice_from_order(
            self.partner,
            note="<p>Customer asked for a pallet.</p>",
        )
        self.assertIn("Customer asked for a pallet.", noted.narration)
        self.assertIn(
            "These products are of EU preferential origin.",
            noted.narration,
        )

        already = self._invoice_from_order(
            self.partner,
            note=plaintext2html(self.invoice_clause.clause),
        )
        self.assertEqual(
            already.narration.count("These products are of EU preferential origin."),
            1,
        )

        plain = self._invoice_from_order(self.plain_partner)
        self.assertFalse(plain.narration)

        self.env.company.terms_type = "plain"
        self.env.company.invoice_terms = "<p>Company terms apply.</p>"
        param_obj.set_param("account.use_invoice_terms", True)
        with_terms = self._invoice_from_order(self.partner)
        self.assertIn("Company terms apply.", with_terms.narration)
        self.assertIn(
            "These products are of EU preferential origin.",
            with_terms.narration,
        )
