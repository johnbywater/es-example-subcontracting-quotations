from eventsourcing.domain.model.aggregate import BaseAggregateRoot

from quotations.exceptions import StatusError


class Quotation(BaseAggregateRoot):
    __subclassevents__ = True

    STATUS_DRAFT = "draft"
    STATUS_PENDING_SUBCONTRACTOR_APPROVAL = "pending_subcontractor_approval"
    STATUS_REJECTED = "rejected"
    STATUS_PENDING_PR = "pending_pr"

    def __init__(self, quotation_number, subcontractor_ref, **kwargs):
        super(Quotation, self).__init__(**kwargs)
        self._quotation_number = quotation_number
        self._subcontractor_ref = subcontractor_ref
        self._status = self.STATUS_DRAFT
        self._line_items = []

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
        self.assert_status(self.STATUS_DRAFT)
        self.__trigger_event__(
            event_class=self.LineItemDetailsAdded,
            remarks=remarks,
            unit_price=unit_price,
            currency=currency,
            quantity=quantity,
        )

    def assert_status(self, status):
        if self._status != status:
            raise StatusError("Status is '%s' not '%s'" % (self._status, status))

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
        self.assert_status(Quotation.STATUS_DRAFT)
        self.__trigger_event__(self.SentToSubcontractor)

    class SentToSubcontractor(BaseAggregateRoot.Event):
        def mutate(self, obj: "Quotation"):
            obj._status = Quotation.STATUS_PENDING_SUBCONTRACTOR_APPROVAL

    def reject(self):
        self.assert_status(self.STATUS_PENDING_SUBCONTRACTOR_APPROVAL)
        self.__trigger_event__(self.Rejected)

    class Rejected(BaseAggregateRoot.Event):
        def mutate(self, obj: "Quotation"):
            obj._status = Quotation.STATUS_REJECTED

    def approve(self):
        self.assert_status(Quotation.STATUS_PENDING_SUBCONTRACTOR_APPROVAL)
        self.__trigger_event__(self.Approved)

    class Approved(BaseAggregateRoot.Event):
        def mutate(self, obj: "Quotation"):
            obj._status = Quotation.STATUS_PENDING_PR


class LineItem(object):
    def __init__(self, remarks, unit_price, currency, quantity):
        self.remarks = remarks
        self.unit_price = unit_price
        self.currency = currency
        self.quantity = quantity
