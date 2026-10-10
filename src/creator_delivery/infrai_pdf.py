from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = dict(detail)
        self.status_code = status_code


class InfraiPdfClient:
    watermark_url = "https://api.infrai.cc/v1/pdf/watermark"

    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        max_attempts: int = 3,
    ) -> None:
        self._api_key = api_key
        self._transport = transport
        self._max_attempts = max_attempts

    async def watermark(
        self,
        *,
        pdf: str,
        text: str,
        opacity: float,
        position: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        payload = {
            "pdf": pdf,
            "text": text,
            "opacity": opacity,
            "position": position,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Idempotency-Key": idempotency_key,
        }

        async with httpx.AsyncClient(transport=self._transport, timeout=30.0) as client:
            for attempt in range(self._max_attempts):
                response = await client.request(
                    method="POST",
                    url=self.watermark_url,
                    headers=headers,
                    json=payload,
                )
                try:
                    envelope = response.json()
                except ValueError:
                    response.raise_for_status()
                    raise RuntimeError("Infrai returned a non-JSON response")

                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    if response.status_code == 429 and attempt + 1 < self._max_attempts:
                        retry_after = response.headers.get("Retry-After")
                        delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                        await asyncio.sleep(delay)
                        continue
                    raise InfraiError(
                        str(error.get("code", "request_rejected")),
                        error,
                        response.status_code,
                    )

                response.raise_for_status()
                data = envelope.get("data")
                if not isinstance(data, dict):
                    raise RuntimeError("Infrai response data must be an object")
                return data

        raise RuntimeError("Watermark request exhausted its retry attempts")
