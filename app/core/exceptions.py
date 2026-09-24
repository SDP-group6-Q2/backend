class AccessDeniedError(Exception):
    """The user's visibility tier or company doesn't allow the requested data.

    Also raised for machines that don't exist or belong to another company, so a
    caller can't tell the two apart (no cross-tenant existence leak).
    """


class NotFoundError(Exception):
    """The requested row doesn't exist inside the user's own company."""


class InvalidCursorError(ValueError):
    """A pagination cursor that couldn't be decoded."""
