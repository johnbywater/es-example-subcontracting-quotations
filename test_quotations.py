from decimal import Decimal
from unittest import TestCase
from uuid import NAMESPACE_URL, uuid5

from eventsourcing.application.notificationlog import NotificationLogReader
from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.domain.model.aggregate import BaseAggregateRoot


class Quotation(BaseAggregateRoot):
    __subclassevents__ = True

    def __init__(self, quotation_number, subcontractor_ref, **kwargs):
        super(Quotation, self).__init__(**kwargs)
        self._quotation_number = quotation_number
        self._status = 'draft'
        self._line_items = []
        self._subcontractor_ref = subcontractor_ref

    @property
    def quotation_number(self):
        return self._quotation_number

    @property
    def status(self):
        return self._status

    @property
    def subcontractor_ref(self):
        return self._subcontractor_ref

    @property
    def line_items(self):
        return self._line_items

    def add_line_item_details(self, remarks, unit_price, currency, quantity):
        self.__trigger_event__(
            event_class=self.LineItemDetailsAdded,
            remarks=remarks,
            unit_price=unit_price,
            currency=currency,
            quantity=quantity,
        )

    class LineItemDetailsAdded(BaseAggregateRoot.Event):
        def mutate(self, obj: "Quotation") -> None:
            obj.line_items.append(
                LineItem(
                    remarks=self.remarks,
                    unit_price=self.unit_price,
                    currency=self.currency,
                    quantity=self.quantity,
                )
            )

    def send_to_subcontractor(self):
        assert self._status == 'draft'
        self.__trigger_event__(self.SentToSubcontractor)

    class SentToSubcontractor(BaseAggregateRoot.Event):
        def mutate(self, obj: "Quotation"):
            obj._status = 'pending_vendor'


class LineItem(object):
    def __init__(self, remarks, unit_price, currency, quantity):
        self.remarks = remarks
        self.unit_price = unit_price
        self.currency = currency
        self.quantity = quantity


class QuotationsApplication(SQLAlchemyApplication):
    persist_event_type = Quotation.Event

    def create_new_quotation(self, quotation_number, subcontractor_ref):
        quotation = Quotation.__create__(
            originator_id=self.create_quotation_id(quotation_number),
            quotation_number=quotation_number,
            subcontractor_ref=subcontractor_ref,
        )
        quotation.__save__()
        return quotation.id

    def create_quotation_id(self, quotation_number):
        return uuid5(NAMESPACE_URL, "/quotations/%s" % quotation_number)

    def get_quotation(self, quotation_number) -> Quotation:
        quotation = self.repository[self.create_quotation_id(quotation_number)]
        assert isinstance(quotation, Quotation)
        return quotation

    def add_line_item_details(
            self, quotation_number, remarks, unit_price, currency, quantity
    ):
        quotation = self.get_quotation(quotation_number)
        quotation.add_line_item_details(remarks, unit_price, currency, quantity)
        quotation.__save__()

    def send_quotation_to_subcontractor(self, quotation_number):
        quotation = self.get_quotation(quotation_number)
        quotation.send_to_subcontractor()
        quotation.__save__()


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
