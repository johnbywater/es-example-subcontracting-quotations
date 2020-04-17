class QuotationsError(Exception):
    pass


class StatusError(QuotationsError):
    pass


class QuotationNotFound(QuotationsError):
    pass