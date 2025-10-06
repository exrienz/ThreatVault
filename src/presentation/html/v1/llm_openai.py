from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sse_starlette import EventSourceResponse

from src.application.dependencies.service_dependency import OpenAIServiceDep

from ..utils import templates

router = APIRouter(prefix="/openai", tags=["LLM Openai"])


@router.get("/", response_class=HTMLResponse)
async def test_stream(
    request: Request,
    service: OpenAIServiceDep,
) -> EventSourceResponse:
    return EventSourceResponse(service.test("HELLO"))


@router.get("/{fn_id}", response_class=HTMLResponse)
async def response(request: Request, service: OpenAIServiceDep, fn_id: UUID):
    await service.get_client()
    return templates.TemplateResponse(
        request, "pages/finding/response/llm_responses.html", {"finding_name_id": fn_id}
    )


@router.get("/{fn_id}/sse", response_class=HTMLResponse)
async def stream_cve_information(
    request: Request,
    service: OpenAIServiceDep,
    fn_id: UUID,
) -> EventSourceResponse:
    return EventSourceResponse(service.streaming_cve(fn_id))
