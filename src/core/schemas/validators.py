"""Shared Pydantic validators for common data types."""

import uuid
from typing import Any


def ensure_uuid(v: Any) -> uuid.UUID:
    """Validate that a given value can be converted to a UUID."""
    if isinstance(v, uuid.UUID):
        return v
    if isinstance(v, str):
        try:
            return uuid.UUID(v)
        except ValueError as exc:
            raise ValueError("Invalid UUID format") from exc
    raise TypeError("UUID string or object required")
