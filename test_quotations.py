from decimal import Decimal
from unittest import TestCase

from quotations.application import QuotationsApplication


class TestQuantationsApplication(TestCase):
    def test_prepare_quotation(self):
        with QuotationsApplication() as app:
            assert isinstance(app, QuotationsApplication)

            # Create a new quotation.
            app.create_new_quotation(
                quotation_number="001", subcontractor_ref="Subcontractor #1",
            )
            quotation = app.get_quotation(quotation_number="001")
            self.assertEqual(quotation.quotation_number, "001")
            self.assertEqual(quotation.subcontractor_ref, "Subcontractor #1")
            self.assertEqual(quotation.status, 'draft')

            # Add a line item to the quotation.
            app.add_line_item_details(
                quotation_number="001",
                remarks="Free text",
                unit_price=Decimal("1000.00"),
                currency="USD",
                quantity=1,
            )
            quotation = app.get_quotation(quotation_number="001")
            self.assertEqual(quotation.line_items[0].remarks, "Free text")
            self.assertEqual(quotation.line_items[0].unit_price, Decimal("1000.00"))
            self.assertEqual(quotation.line_items[0].currency, "USD")
            self.assertEqual(quotation.line_items[0].quantity, 1)

            # Add a second line item.
            app.add_line_item_details(
                quotation_number="001",
                remarks="Some other free text",
                unit_price=Decimal("2000.00"),
                currency="USD",
                quantity=1,
            )
            quotation = app.get_quotation(quotation_number="001")
            self.assertEqual(len(quotation.line_items), 2)

            # Send quotation to subcontractor.
            app.send_quotation_to_subcontractor(quotation_number="001")
            quotation = app.get_quotation(quotation_number="001")
            self.assertEqual(quotation.status, 'pending_vendor')
