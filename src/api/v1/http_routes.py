"""
Shared router configuration for all v1 HTTP endpoints.

This module defines a base FastAPI APIRouter instance (`v1_router`) that enforces:
- Consistent URL prefix: `/api/v1`
- Common metadata (tags, descriptions)
- Uniform error responses

All v1 route modules should import and use this router to ensure consistency
and easy future versioning (e.g., adding /api/v2 later).
"""

from fastapi import APIRouter


# Create a single, reusable router for all v1 endpoints
v1_router = APIRouter(
    prefix="/api/v1",
    tags=["Players"],
    responses={
        404: {"description": "The requested resource was not found"},
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "string_too_short",
                                "loc": ["body", "username"],
                                "msg": "String should have at least 3 characters",
                                "input": "ab",
                            }
                        ]
                    }
                }
            },
        },
    },
    # Optional: Add dependencies here later (e.g., auth, rate limiting)
    # dependencies=[Depends(oauth2_scheme)]
)
