"""Builder for creating standardized responses."""

from typing import Optional, Dict, Any
from src.api.v1.schemas.place_ships import StandardResponse


class ResponseBuilder:
    """Builder for creating standardized responses."""

    @staticmethod
    def error(message: str, action: str = "error") -> StandardResponse:
        """Create an error response."""
        return StandardResponse(
            status="error",
            message=message,
            action=action,
            data=""
        )

    @staticmethod
    def success(
        message: str,
        action: str,
        data: Optional[Dict[Any, Any]] = None
    ) -> StandardResponse:
        """Create a success response."""
        return StandardResponse(
            status="success",
            message=message,
            action=action,
            data=data or {}
        )

    @staticmethod
    def validation_error(field: str, action: str) -> StandardResponse:
        """Create a validation error response."""
        return ResponseBuilder.error(
            f"Invalid {field} value",
            f"error_{action}"
        )
