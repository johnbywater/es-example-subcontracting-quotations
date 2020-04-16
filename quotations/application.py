from uuid import NAMESPACE_URL, uuid5

from eventsourcing.application.sqlalchemy import SQLAlchemyApplication

from quotations.domainmodel import Quotation


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

    def subcontractor_rejects_quotation(self, quotation_number):
        quotation = self.get_quotation(quotation_number)
        quotation.reject()
        quotation.__save__()

    def subcontractor_approves_quotation(self, quotation_number):
        quotation = self.get_quotation(quotation_number)
        quotation.approve()
        quotation.__save__()
