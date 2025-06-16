from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request

from src.application.dependencies import (
    CommentServiceDep,
    FindingServiceDep,
    ProductServiceDep,
)
from src.application.schemas.finding import ITSRemark
from src.domain.constant import FnStatusEnum
from src.presentation.html.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(prefix="/finding", tags=["finding"])


# TODO: HTML file looks confusing
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
            "data": data,
            "product": product,
            "findings_dict": findings_dict,
            "finding_name_id": finding_name_id,
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


@router.delete("/comment/{comment_id}")
async def delete_finding_comment(
    request: Request,
    service: CommentServiceDep,
    comment_id: UUID,
):
    await service.delete(comment_id)


@router.delete(
    "/comment/{comment_id}/admin",
    dependencies=[Depends(PermissionChecker(["comment:delete-any"]))],
)
async def delete_finding_comment_admin(
    request: Request,
    service: CommentServiceDep,
    comment_id: UUID,
):
    await service.delete(comment_id, bypass=True)


@router.get("/{finding_name_id}/pic-list")
async def get_pic_list(
    request: Request,
    service: ProductServiceDep,
    finding_service: FindingServiceDep,
    finding_name_id: UUID,
):
    finding = await finding_service.get_by_id_extended(finding_name_id)
    users = await service.get_owners_by_product_id(finding.product_id)
    return templates.TemplateResponse(
        request,
        "pages/finding/component/pic.html",
        {
            "data": users,
        },
    )


@router.post("/{finding_name_id}/remark")
async def create_remark(
    request: Request,
    data: Annotated[ITSRemark, Form()],
    service: ProductServiceDep,
    finding_service: FindingServiceDep,
    finding_name_id: UUID,
):
    finding_name = await finding_service.get_by_id_extended(finding_name_id)
    users = await service.get_owners_by_product_id(finding_name.product_id)
    valid_pic = []
    if data.pic_list:
        for user in users:
            if user.id in data.pic_list:
                valid_pic.append(user.username)
    filters = {"id": [str(finding.id) for finding in finding_name.findings]}
    remarks = f"""
    PIC:
    {valid_pic}

    Delay Reason:
    {data.reason}

    ITS Remark:
    {data.remark}
    """
    update_dict = {
        "delay_untill": data.target_date,
        "remark": remarks,
        "status": FnStatusEnum.EXEMPTION,
    }
    await finding_service.bulk_update(filters, update_dict)
    return templates.TemplateResponse(
        request,
        "pages/finding/response/add_remark.html",
    )
