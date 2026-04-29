from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": jsonable_encoder(details),
            }
        },
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "请求失败"
    details = None if isinstance(exc.detail, str) else exc.detail
    return _error_response(
        status_code=exc.status_code,
        code=f"HTTP_{exc.status_code}",
        message=message,
        details=details,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="请求参数校验失败",
        details=exc.errors(),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return _error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="服务器内部错误",
    )
