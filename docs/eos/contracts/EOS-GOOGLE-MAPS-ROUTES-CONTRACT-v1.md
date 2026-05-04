# EOS Google Maps Routes Contract v1

Status: fake-provider readiness only. Live Google Maps or Routes API calls are not verified.

## Route Request

```python
RouteRequest(
    origin="Office Example",
    destination="Clinic Example",
    mode="driving",
    departure_time="2026-05-07T12:30:00",
)
```

Allowed modes:

```text
driving
walking
transit
cycling
```

Invalid modes fall back to `driving`.

## Route Estimate

`RouteEstimate` contains origin, destination, mode, duration minutes, optional traffic duration, optional distance text, provider, and `live_verified`.

## Fake Provider

The fake provider is deterministic, makes no network calls, and always returns `live_verified=false`.

## Live Contract Preparation

Later live verification should compare fake-provider fields with Google Routes output and should not store route history, raw addresses, latitude/longitude history, or API keys.
