from decimal import Decimal
from unittest import TestCase

from eventsourcing.application.notificationlog import NotificationLogReader
from eventsourcing.application.popo import PopoApplication
from eventsourcing.system.definition import AbstractSystemRunner

from quotations.applications.notifications import NotificationsApplication
from quotations.applications.quotations import QuotationsApplication
from quotations.domainmodel import EmailNotification, Quotation
from quotations.exceptions import QuotationNotFound, StatusError
from quotations.system import QuotationsSystem


class TestQuotationsApplication(TestCase):
    def test_prepare_quotation(self):
        with QuotationsApplication.mixin(PopoApplication)() as app:
            app: QuotationsApplication

            # Create a new quotation.
            app.create_new_quotation(
                quotation_number="001", subcontractor_ref="Subcontractor #1",
            )
            quotation = app.get_quotation(quotation_number="001")
            self.assertEqual(quotation.quotation_number, "001")
            self.assertEqual(quotation.subcontractor_ref, "Subcontractor #1")
            self.assertEqual(quotation.status, Quotation.STATUS_DRAFT)

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
            self.assertEqual(
                quotation.status, Quotation.STATUS_PENDING_SUBCONTRACTOR_APPROVAL
            )

            # Can't send twice.
            with self.assertRaises(StatusError):
                app.send_quotation_to_subcontractor(quotation_number="001")

            # Can't add line item after sent to subcontractor.
            with self.assertRaises(StatusError):
                app.add_line_item_details(
                    quotation_number="001",
                    remarks="Some other free text",
                    unit_price=Decimal("2000.00"),
                    currency="USD",
                    quantity=1,
                )

            # Quotation not found.
            with self.assertRaises(QuotationNotFound):
                app.get_quotation("002")

    def test_reject_prepared_quotation(self):
        with QuotationsApplication.mixin(PopoApplication)() as app:
            app: QuotationsApplication
            app.create_new_quotation(
                quotation_number="001", subcontractor_ref="Subcontractor #1",
            )
            app.add_line_item_details(
                quotation_number="001",
                remarks="Free text",
                unit_price=Decimal("1000.00"),
                currency="USD",
                quantity=1,
            )
            app.send_quotation_to_subcontractor(quotation_number="001")

            app.reject_quotation(quotation_number="001")
            quotation = app.get_quotation(quotation_number="001")
            self.assertEqual(quotation.status, Quotation.STATUS_REJECTED)

            # Check can't reject or approve once rejected.
            with self.assertRaises(StatusError):
                app.reject_quotation(quotation_number="001")

            with self.assertRaises(StatusError):
                app.approve_quotation(quotation_number="001")

    def test_approve_prepared_quotation(self):
        with QuotationsApplication.mixin(PopoApplication)() as app:
            app: QuotationsApplication
            app.create_new_quotation(
                quotation_number="001", subcontractor_ref="Subcontractor #1",
            )
            app.add_line_item_details(
                quotation_number="001",
                remarks="Free text",
                unit_price=Decimal("1000.00"),
                currency="USD",
                quantity=1,
            )
            app.send_quotation_to_subcontractor(quotation_number="001")

            app.approve_quotation(quotation_number="001")
            quotation = app.get_quotation(quotation_number="001")
            self.assertEqual(quotation.status, Quotation.STATUS_PENDING_PR)

            # Check can't reject or approve once approved.
            with self.assertRaises(StatusError):
                app.reject_quotation(quotation_number="001")

            with self.assertRaises(StatusError):
                app.approve_quotation(quotation_number="001")


class TestQuotationsSystem(TestCase):
    def test_notifications(self):
        with QuotationsSystem(infrastructure_class=PopoApplication) as runner:
            runner: AbstractSystemRunner
            quotations = runner.get(QuotationsApplication)
            notifications = runner.get(NotificationsApplication)

            quotations.create_new_quotation(
                quotation_number="001", subcontractor_ref="Subcontractor #1",
            )
            quotations.add_line_item_details(
                quotation_number="001",
                remarks="Free text",
                unit_price=Decimal("1000.00"),
                currency="USD",
                quantity=1,
            )

            reader = NotificationLogReader(notifications.notification_log)
            self.assertEqual(len(list(reader.read())), 0)

            quotations.send_quotation_to_subcontractor(quotation_number="001")

            notification_events = list(
                map(notifications.get_event_from_notification, reader.read())
            )
            self.assertEqual(len(notification_events), 1)
            self.assertIsInstance(notification_events[0], EmailNotification.Created)
            email: EmailNotification.Created = notification_events[0]
            self.assertEqual(email.quotation_number, "001")
            self.assertEqual(email.subcontractor_ref, "Subcontractor #1")
