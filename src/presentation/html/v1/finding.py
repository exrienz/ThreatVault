from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from src.application.services import FindingService, ProductService
from src.config import sidebar_items

from ..utils import templates

router = APIRouter(prefix="/finding", tags=["finding"])
finding_service = Annotated[FindingService, Depends()]


@router.get("/{finding_name_id}")
async def get_finding(
    request: Request,
    service: finding_service,
    product_service: Annotated[ProductService, Depends()],
    finding_name_id: UUID,
):
    data = await service.get_by_id_extended(finding_name_id)
    product = await product_service.get_by_id(data.product_id)
    return templates.TemplateResponse(
        request,
        "pages/finding/index.html",
        {"sidebarItems": sidebar_items, "data": data, "product": product},
    )
