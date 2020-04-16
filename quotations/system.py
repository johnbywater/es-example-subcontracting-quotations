from eventsourcing.system.definition import System

from quotations.applications.notifications import NotificationsApplication
from quotations.applications.quotations import QuotationsApplication


class QuotationsSystem(System):
    def __init__(self, **kwargs):
        super(QuotationsSystem, self).__init__(
            QuotationsApplication | NotificationsApplication, **kwargs
        )
