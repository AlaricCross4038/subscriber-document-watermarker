from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI, HTTPException

from .delivery_workflow import DeliveryRequest, DeliveryResult, prepare_delivery
from .infrai_pdf import InfraiError, InfraiPdfClient

app = FastAPI(title="Creator document delivery")


@app.post("/deliveries", response_model=DeliveryResult)
async def create_delivery(request: DeliveryRequest) -> DeliveryResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    try:
        return await prepare_delivery(request, InfraiPdfClient(api_key))
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except (RuntimeError, OSError) as exc:
        raise HTTPException(status_code=502, detail="Document processing did not complete") from exc


def run() -> None:
    uvicorn.run("creator_delivery.delivery_api:app", host="127.0.0.1", port=8000)
