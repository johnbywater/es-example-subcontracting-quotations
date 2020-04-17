from uuid import NAMESPACE_URL, UUID, uuid5

from eventsourcing.application.process import ProcessApplication
from eventsourcing.exceptions import RepositoryKeyError

from quotations.domainmodel import Quotation
from quotations.exceptions import QuotationNotFound


class QuotationsApplication(ProcessApplication):
    def create_new_quotation(self, quotation_number, subcontractor_ref) -> None:
        quotation = Quotation.__create__(
            originator_id=self.create_quotation_id(quotation_number),
            quotation_number=quotation_number,
            subcontractor_ref=subcontractor_ref,
        )
        self.save(quotation)

    def create_quotation_id(self, quotation_number) -> UUID:
        return uuid5(NAMESPACE_URL, "/quotations/%s" % quotation_number)

    def get_quotation(self, quotation_number) -> Quotation:
        try:
            quotation = self.repository[self.create_quotation_id(quotation_number)]
        except RepositoryKeyError:
            raise QuotationNotFound(quotation_number)
        else:
            assert isinstance(quotation, Quotation), type(quotation)
            return quotation

    def add_line_item_details(
        self, quotation_number, remarks, unit_price, currency, quantity
    ) -> None:
        quotation = self.get_quotation(quotation_number)
        quotation.add_line_item_details(remarks, unit_price, currency, quantity)
        self.save(quotation)

    def send_quotation_to_subcontractor(self, quotation_number) -> None:
        quotation = self.get_quotation(quotation_number)
        quotation.send_to_subcontractor()
        self.save(quotation)

    def reject_quotation(self, quotation_number) -> None:
        quotation = self.get_quotation(quotation_number)
        quotation.reject()
        self.save(quotation)

    def approve_quotation(self, quotation_number) -> None:
        quotation = self.get_quotation(quotation_number)
        quotation.approve()
        self.save(quotation)
