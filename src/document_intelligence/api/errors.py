from fastapi import Request, status
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Base for errors rendered via this API's `{"error": {"code", "message"}}` envelope."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValidationError(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_submission"


class SubmissionTooLargeError(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "submission_too_large"


class SubmissionTooManyPagesError(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "submission_too_many_pages"


class AuthError(ApiError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class NotFoundError(ApiError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(ApiError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
