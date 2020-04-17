from eventsourcing.application.decorators import applicationpolicy
from eventsourcing.application.process import ProcessApplication

from quotations.domainmodel import EmailNotification, Quotation


class NotificationsApplication(ProcessApplication):
    @applicationpolicy
    def policy(self, repository, event):
        pass

    @policy.register(Quotation.SentToSubcontractor)
    def _(self, _, event):
        return EmailNotification.__create__(
            quotation_number=event.quotation_number,
            subcontractor_ref=event.subcontractor_ref,
        )
