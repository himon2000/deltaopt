"""Vendor-neutral export boundary, not an integration with Semantica APIs."""
from typing import Protocol

from .graph import to_rdf
from .temporal import Store


class GraphSink(Protocol):
    def ingest(self, payload: dict) -> None: ...


def export(store: Store) -> dict:
    return {
        "schema": "deltaopt-bridge-v0.1",
        "integration": "vendor-neutral; native Semantica adapter pending",
        "versions": [{
            "id": v.number, "parent": v.parent, "valid_from": v.valid_from,
            "recorded_at": v.recorded_at, "source": v.source,
            "restored_from": v.restored_from,
            "patch": v.patch.model_dump() if v.patch else None,
            "model": v.model.model_dump(),
            "rdf_turtle": to_rdf(v.model).serialize(format="turtle"),
        } for v in store.versions],
    }


def publish(store: Store, sink: GraphSink) -> None:
    """Caller supplies an adapter implementing ingest; no credentials are read."""
    sink.ingest(export(store))
