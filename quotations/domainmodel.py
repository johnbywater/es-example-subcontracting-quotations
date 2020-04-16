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

    def reject(self):
        self.__trigger_event__(self.Rejected)

    class Rejected(BaseAggregateRoot.Event):
        def mutate(self, obj: "Quotation"):
            obj._status = 'rejected'

    def approve(self):
        self.__trigger_event__(self.Approved)

    class Approved(BaseAggregateRoot.Event):
        def mutate(self, obj: "Quotation"):
            obj._status = 'pending_pr'


class LineItem(object):
    def __init__(self, remarks, unit_price, currency, quantity):
        self.remarks = remarks
        self.unit_price = unit_price
        self.currency = currency
        self.quantity = quantity