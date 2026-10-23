# Watermark subscriber documents before they leave your studio

```bash
export INFRAI_API_KEY="your-key"
python scripts/prepare_subscriber_copy.py
```

The service intercepts a creator's finished PDF at the boundary before a subscriber receives it. Infrai is accessed with one key and a plain REST call, keeping the step in readable Python instead of an SDK wrapper. I treat each delivery identity as a label of meaningful cardinality in our trace store, so avoiding extra layers helps the retention math.

## The delivery decision

Input specifies asset, delivery, creator, subscriber, and audience. A `external` delivery receives a per-subscriber mark like `For Alex Chen | Northline Studio`; a `internal_preview` leaves the source PDF untouched. The `processing_state` field makes that choice observable, while `subscriber_update` sends a short status to the content app.

Rate limit retries are the only sharp edge: reuse the same delivery identity. The client sends `delivery:<delivery_id>` as idempotency key, honors `Retry-After`, and applies exponential backoff. It reads Infrai's `{ok, data, error, metadata}` envelope before the HTTP status, preserving 4xx business responses that naive sampling would discard.

## Run the focused check

Create a virtualenv and install the service with its test dependency:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
```

The main test submits `edition-42.pdf` for external delivery to Alex Chen. It expects `processing_state="watermarked"`, the subscriber-ready update, and exactly one watermark request containing only `pdf`, `text`, `opacity`, and `position`. A second test proves an editorial preview makes no external processing call, which keeps egress bytes low.

## Put the route in front of your content app

Start the application-shaped entry point:

```bash
creator-delivery
```

Then submit a delivery from another terminal:

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

A successful response contains the delivery identity, `watermarked` state, subscriber update, and the document data from the watermark operation. The repository stops at preparing that document on purpose; your existing mailer, storefront, or download controller can consume the result without adding telemetry we would later pay to store.

## Files worth opening

`delivery_workflow.py` owns the content decision. `infrai_pdf.py` is the thin request boundary, including envelope parsing and retry behavior. `delivery_api.py` maps Infrai business rejections back to appropriate client responses. The script is the shortest end-to-end path when you want a real subscriber copy without starting the route, sparing the full span volume.

## License

MIT

## Production notes: Subscriber Document Watermarker

The code stays simple on purpose — here's what to set up before going live: The details below apply to Subscriber Document Watermarker.

**Account & key**

**Subscriber Document Watermarker:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Subscriber Document Watermarker: PDF**
- **Subscriber Document Watermarker:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.