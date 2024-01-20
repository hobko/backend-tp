from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from config_loggers.logConfig import setup_logger

logger = setup_logger()


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as exc:
            return JSONResponse(
                content={"detail": exc.detail},
                status_code=exc.status_code,
            )
        except Exception as e:
            logger.exception(f"Unexpected error: {str(e)}")
            return JSONResponse(
                content={"detail": "Internal Server Error"},
                status_code=500,
            )
