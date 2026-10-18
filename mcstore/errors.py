class MCStoreError(Exception):
    """Base class for expected domain errors."""


class NotFoundError(MCStoreError):
    pass


class ConflictError(MCStoreError):
    pass


class InsufficientFundsError(MCStoreError):
    pass
