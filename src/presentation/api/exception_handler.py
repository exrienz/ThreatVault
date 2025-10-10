from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def httpException(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(
            content="Please provide valid api key!", status_code=exc.status_code
        )
    return JSONResponse(content=str(exc.detail), status_code=exc.status_code)


exception_handlers = {
    HTTPException: httpException,
}
