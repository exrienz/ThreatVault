from fastapi import Request
from fastapi.responses import JSONResponse

from src.presentation.api.exception_handler import exception_handlers as api_exceptions
from src.presentation.html.exception_handler import (
    exception_handlers as html_exceptions,
)


class GlobalExceptionHandler:
    def is_api_request(self, request: Request) -> bool:
        return request.headers.get("accept", "") == "application/json"

    def __call__(self, request: Request, exc: Exception):
        exc_dict = api_exceptions if self.is_api_request(request) else html_exceptions
        func = exc_dict.get(type(exc))
        if func:
            return func(request, exc)
        return JSONResponse({"error": "Internal server error"}, status_code=500)

    # def __call__(self, request: Request, exc: Exception):
    #     if self.is_api_request(request):
    #         exc_dict = self.registry.get("api", {})
    #         func = exc_dict.get(type(exc))
    #         if func:
    #             return func(request, exc)
    #     else:
    #         exc_dict = self.registry.get("html", {})
    #         func = exc_dict.get(type(exc))
    #         if func:
    #             return func(request, exc)
    #     exc_dict = self.registry.get("default", {})
    #     func = exc_dict.get(type(exc))
    #     if func:
    #         return func(request, exc)
    #     return JSONResponse({"error": "Internal server error"}, status_code=500)
