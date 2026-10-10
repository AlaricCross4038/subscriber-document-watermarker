from __future__ import annotations

import asyncio
from typing import Any

from creator_delivery.delivery_workflow import DeliveryRequest, prepare_delivery


class RecordingWatermarker:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def watermark(self, **request: Any) -> dict[str, Any]:
        self.calls.append(request)
        return {"pdf": "https://cdn.example.com/deliveries/alex-watermarked.pdf"}


def test_external_delivery_watermarks_a_subscriber_copy() -> None:
    watermarker = RecordingWatermarker()
    request = DeliveryRequest(
        delivery_id="edition-42-alex",
        asset_pdf="https://assets.example.com/edition-42.pdf",
        audience="external",
        subscriber_name="Alex Chen",
        creator_name="Northline Studio",
        opacity=0.2,
        position="center",
    )

    result = asyncio.run(prepare_delivery(request, watermarker))

    assert result.processing_state == "watermarked"
    assert result.subscriber_update == "Subscriber copy is ready to share"
    assert result.document["pdf"].endswith("alex-watermarked.pdf")
    assert watermarker.calls == [
        {
            "pdf": "https://assets.example.com/edition-42.pdf",
            "text": "For Alex Chen | Northline Studio",
            "opacity": 0.2,
            "position": "center",
            "idempotency_key": "delivery:edition-42-alex",
        }
    ]


def test_internal_preview_keeps_the_source_document() -> None:
    watermarker = RecordingWatermarker()
    request = DeliveryRequest(
        delivery_id="edition-42-review",
        asset_pdf="https://assets.example.com/edition-42.pdf",
        audience="internal_preview",
        subscriber_name="Editorial desk",
        creator_name="Northline Studio",
    )

    result = asyncio.run(prepare_delivery(request, watermarker))

    assert result.processing_state == "original_retained"
    assert result.document == {"pdf": request.asset_pdf}
    assert watermarker.calls == []
