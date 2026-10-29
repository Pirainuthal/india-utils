"""Exception types shared by every validator in :mod:`india_utils`."""

from __future__ import annotations

__all__ = ["ValidationError"]


class ValidationError(ValueError):
    """Raised when an identifier or amount is malformed.

    It subclasses :class:`ValueError`, so existing ``except ValueError``
    handlers keep working. ``field`` names the kind of value that failed
    (``"gstin"``, ``"pan"``, ``"amount"``, ...) and ``reason`` is a short,
    human-readable explanation suitable for showing to an end user.
    """

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"invalid {field}: {reason}")
        self.field = field
        self.reason = reason
