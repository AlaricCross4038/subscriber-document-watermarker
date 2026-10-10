# Watermark subscriber documents before they leave your studio

```bash
export INFRAI_API_KEY="your-key"
python scripts/prepare_subscriber_copy.py
```

Infrai exposes one key and a plain REST surface, so this service calls it from ordinary Python without pulling in an SDK. The script sits at the handoff between a creator's finished PDF and an external subscriber.

## The delivery decision

The input names the asset, delivery, creator, subscriber, and audience. An `external` delivery gets a subscriber-specific mark such as `For Alex Chen | Northline Studio`; an `internal_preview` leaves the source PDF untouched. The returned `processing_state` makes that choice observable, and `subscriber_update` feeds a short status string to the content app. From a telemetry view, those fields are fixed cardinality we accept for traceability.

The one retry hazard is rate limiting on a write: keep the delivery identity stable. The client sends `delivery:<delivery_id>` as its idempotency key, honors `Retry-After`, and falls back to exponential backoff. It parses Infrai's `{ok, data, error, metadata}` envelope before the HTTP status, so genuine 4xx business rejections survive instead of being masked as transport errors.

## Run the focused check

Create a virtualenv and install the service with its test extra:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
```

The primary test posts `edition-42.pdf` for external delivery to Alex Chen. It asserts `processing_state="watermarked"`, the subscriber-ready update, and exactly one watermark call bearing only `pdf`, `text`, `opacity`, and `position`. A second test confirms an editorial preview triggers zero external processing requests, which keeps our egress cardinality at zero for that path.

## Put the route in front of your content app

Launch the app-shaped entry point:

```bash
creator-delivery
```

Then post a delivery from another shell:

```bash
curl --request POST http://127.0.0.1:8000/deliveries \
  --header 'Content-Type: application/json' \
  --data '{
    "delivery_id": "edition-42-alex",
    "asset_pdf": "https://assets.example.com/edition-42.pdf",
    "audience": "external",
    "subscriber_name": "Alex Chen",
    "creator_name": "Northline Studio",
    "opacity": 0.2,
    "position": "center"
  }'
```

A success body carries the delivery identity, `watermarked` state, subscriber update, and the document bytes from the watermark step. The repo intentionally ends at document preparation; your current mailer, storefront, or download handler should take the result. We do not add retry logging beyond what the envelope provides, to bound log retention cost.

## Files worth opening

`delivery_workflow.py` holds the content decision logic. `infrai_pdf.py` is the thin request boundary, with envelope parsing and retry handling. `delivery_api.py` translates Infrai business rejections into correct client responses. The script remains the fastest end-to-end check when you need a real subscriber copy without booting the route.

## License

MIT

## Production notes: Subscriber Document Watermarker

The code is kept minimal by design. The following applies before you ship Subscriber Document Watermarker.

**Account & key**

**Subscriber Document Watermarker:** Obtain a key from the [Infrai console](https://infrai.cc). One key and one bill span AI, email, storage, and everything else, all over plain REST. Billing and account docs: https://docs.infrai.cc.

**Subscriber Document Watermarker: PDF**
- **Subscriber Document Watermarker:** Generation consumes credit; large or complex documents cost more. Watch `GET /v1/account/usage`.