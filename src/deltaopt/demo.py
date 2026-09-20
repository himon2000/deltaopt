"""Deterministic 8h -> 6h production-planning vertical slice."""
from .graph import impact
from .model import GraphPatch, Model
from .solver import verify
from .temporal import Store


def initial_model():
    return Model.model_validate({
        "capacity": 8.0, "source": "R0: maximize profit with 8 machine hours",
        "products": [
            {"id": "A", "processing_time": 2.0, "profit": 3.0,
             "minimum": 0, "maximum": 4, "category": "standard"},
            {"id": "B", "processing_time": 3.0, "profit": 5.0,
             "minimum": 0, "maximum": 2, "category": "premium"},
        ],
    })


def capacity_patch(version=1, old=8.0, value=6.0, valid_from=1):
    return GraphPatch.model_validate({
        "base_version": version, "source": "R1: available capacity changed",
        "valid_from": valid_from,
        "operations": [{"path": "/capacity", "old": old, "value": value}],
    })


def run():
    store = Store(initial_model())
    before = verify(store.head.model)
    patch = capacity_patch()
    store.commit(patch, recorded_at=2)
    after = verify(store.head.model)
    store.rollback(1, valid_from=3, recorded_at=3, source="R2: restore original plan")
    return {
        "mode": "offline deterministic replay; no LLM experiment",
        "versions": [v.number for v in store.versions],
        "capacity": [8.0, 6.0], "objective": [before.objective, after.objective],
        "impact": impact(initial_model(), ["/capacity"]),
        "patched_paths": [op.path for op in patch.operations],
        "earlier_known_capacity": store.snapshot(valid_at=1, known_at=1).capacity,
        "later_known_capacity": store.snapshot(valid_at=1, known_at=2).capacity,
        "rollback_objective": verify(store.head.model).objective,
    }
