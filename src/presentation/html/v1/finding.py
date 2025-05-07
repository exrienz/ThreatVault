from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request

from src.application.dependencies import (
    CommentServiceDep,
    FindingServiceDep,
    ProductServiceDep,
)
from src.config import sidebar_items
from src.domain.constant import FnStatusEnum

from ..utils import templates

router = APIRouter(prefix="/finding", tags=["finding"])


@router.get("/{finding_name_id}")
async def get_finding(
    request: Request,
    service: FindingServiceDep,
    product_service: ProductServiceDep,
    finding_name_id: UUID,
):
    data = await service.get_by_id_extended(finding_name_id)
    product = await product_service.get_by_id(data.product_id)
    findings = [
        finding for finding in data.findings if finding.status != FnStatusEnum.CLOSED
    ]
    findings_dict: dict[str, list] = {}
    for finding in findings:
        if findings_dict.get(finding.host):
            findings_dict[finding.host].append(finding)
        else:
            findings_dict[finding.host] = [finding]
    return templates.TemplateResponse(
        request,
        "pages/finding/index.html",
        {
            "sidebarItems": sidebar_items,
            "data": data,
            "product": product,
            "findings_dict": findings_dict,
        },
    )


@router.get("/{finding_name_id}/comments")
async def get_all_comment(
    request: Request,
    service: CommentServiceDep,
    finding_name_id: UUID,
):
    comments = await service.get_by_finding_name_id(finding_name_id)
    return templates.TemplateResponse(
        request,
        "pages/finding/component/comments.html",
        {
            "finding_name_id": finding_name_id,
            "comments": comments,
        },
    )


@router.post("/{finding_name_id}/comment")
async def comment_finding(
    request: Request,
    service: CommentServiceDep,
    finding_name_id: UUID,
    comment: Annotated[str, Form()],
):
    data = await service.create(finding_name_id, comment)
    return templates.TemplateResponse(
        request,
        "pages/finding/response/add_comment.html",
        {
            "comment": data,
        },
    )


@router.delete("/{finding_name_id}/comment/{comment_id}")
async def delete_finding_comment(
    request: Request,
    service: CommentServiceDep,
    finding_name_id: UUID,
    comment_id: UUID,
):
    await service.delete(comment_id)
