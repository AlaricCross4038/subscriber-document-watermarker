from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class DeliveryRequest(BaseModel):
    delivery_id: str = Field(min_length=1)
    asset_pdf: str = Field(min_length=1)
    audience: Literal["external", "internal_preview"]
    subscriber_name: str = Field(min_length=1)
    creator_name: str = Field(min_length=1)
    opacity: float = Field(default=0.18, ge=0.0, le=1.0)
    position: str = "center"


class DeliveryResult(BaseModel):
    delivery_id: str
    processing_state: Literal["watermarked", "original_retained"]
    subscriber_update: str
    document: dict[str, Any]


class Watermarker(Protocol):
    async def watermark(
        self,
        *,
        pdf: str,
        text: str,
        opacity: float,
        position: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        raise AssertionError("Protocol methods are supplied by the client")


async def prepare_delivery(request: DeliveryRequest, watermarker: Watermarker) -> DeliveryResult:
    if request.audience == "internal_preview":
        return DeliveryResult(
            delivery_id=request.delivery_id,
            processing_state="original_retained",
            subscriber_update="Internal preview prepared",
            document={"pdf": request.asset_pdf},
        )

    watermark_text = f"For {request.subscriber_name} | {request.creator_name}"
    document = await watermarker.watermark(
        pdf=request.asset_pdf,
        text=watermark_text,
        opacity=request.opacity,
        position=request.position,
        idempotency_key=f"delivery:{request.delivery_id}",
    )
    return DeliveryResult(
        delivery_id=request.delivery_id,
        processing_state="watermarked",
        subscriber_update="Subscriber copy is ready to share",
        document=document,
    )
