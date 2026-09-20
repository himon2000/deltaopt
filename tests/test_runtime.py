import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from rdflib import Graph

from deltaopt.agent import ReplayProvider, propose
from deltaopt.demo import capacity_patch, initial_model, run
from deltaopt.evaluation import evaluate
from deltaopt.graph import DATA, OPT, to_rdf
from deltaopt.model import GraphPatch
from deltaopt.patch import apply
from deltaopt.semantic import verify
from deltaopt.semantica_bridge import export, publish
from deltaopt.solver import verify as solve
from deltaopt.temporal import Store


def modified(path, old, value):
    data = capacity_patch().model_dump()
    data["operations"] = [{"path": path, "old": old, "value": value}]
    return GraphPatch.model_validate(data)


def test_demo_and_rollback():
    result = run()
    assert result["objective"] == [13.0, 10.0]
    assert result["rollback_objective"] == 13.0
    assert result["versions"] == [1, 2, 3]


def test_local_patch_preserves_unaffected_state():
    model = initial_model()
    result = apply(model, capacity_patch(), 1)
    assert model.capacity == 8
    assert result.capacity == 6
    assert result.products == model.products
    assert verify(result)[0]


@pytest.mark.parametrize("path,old,value", [
    ("/products/A/category", "standard", "alien"),
    ("/capacity", 8.0, -1.0),
    ("/source", "anything", "tampered"),
    ("/capacity", 9.0, 6.0),
    ("/products/missing/profit", 3.0, 8.0),
])
def test_rejected_patch_is_atomic(path, old, value):
    store = Store(initial_model())
    before = store.versions
    with pytest.raises(ValueError):
        store.commit(modified(path, old, value), recorded_at=1)
    assert store.versions == before


def test_solver_infeasibility_does_not_commit():
    store = Store(initial_model())
    patch = capacity_patch().model_dump()
    patch["operations"] = [
        {"path": "/products/A/minimum", "old": 0, "value": 4},
        {"path": "/products/B/minimum", "old": 0, "value": 1},
    ]
    patch = GraphPatch.model_validate(patch)
    candidate = apply(store.head.model, patch, 1)
    assert verify(candidate)[0]
    assert solve(candidate).status == "infeasible"
    with pytest.raises(ValueError, match="solver"):
        store.commit(patch, recorded_at=1)
    assert store.head.number == 1


def test_stale_version_and_duplicate_path():
    store = Store(initial_model())
    store.commit(capacity_patch(), recorded_at=1)
    with pytest.raises(ValueError, match="stale"):
        store.commit(capacity_patch(), recorded_at=2)
    patch = capacity_patch().model_dump()
    patch["operations"] *= 2
    with pytest.raises(ValueError, match="duplicate"):
        apply(initial_model(), GraphPatch.model_validate(patch), 1)


def test_late_revision_and_defensive_copies():
    store = Store(initial_model())
    store.commit(capacity_patch(valid_from=2), recorded_at=8)
    assert store.snapshot(2, 7).capacity == 8
    assert store.snapshot(2, 8).capacity == 6
    assert store.snapshot(1, 8).capacity == 8
    store.head.model.capacity = 99
    store.versions[0].model.capacity = 99
    assert store.head.model.capacity == 6
    assert store.snapshot(0, 0).capacity == 8
    with pytest.raises(ValueError):
        store.rollback(1, valid_from=3, recorded_at=8, source="rollback")


def test_schema_rejects_extra_and_nan():
    patch = capacity_patch().model_dump()
    patch["execute"] = "arbitrary code"
    with pytest.raises(ValidationError):
        GraphPatch.model_validate(patch)
    with pytest.raises(ValueError):
        modified("/capacity", 8.0, float("nan"))


def test_rdf_and_resource_parity():
    root = Path(__file__).resolve().parents[1]
    for name in ["optimization.ttl", "shapes.ttl"]:
        assert (root / "ontology" / name).read_bytes() == (
            root / "src/deltaopt/resources" / name).read_bytes()
        assert len(Graph().parse(root / "ontology" / name, format="turtle")) > 0
    graph = to_rdf(initial_model())
    assert (DATA.capacity_constraint, OPT.derivedFrom, DATA.requirement) in graph


def test_bridge_retains_patch_source_and_rollback():
    store = Store(initial_model())
    store.commit(capacity_patch(), recorded_at=1)
    store.rollback(1, valid_from=2, recorded_at=2, source="restore")
    payload = export(store)
    assert payload["versions"][1]["patch"]["source"] == capacity_patch().source
    assert payload["versions"][2]["restored_from"] == 1
    json.dumps(payload)

    class Sink:
        def ingest(self, payload):
            self.payload = payload
    sink = Sink()
    publish(store, sink)
    assert len(sink.payload["versions"]) == 3


def test_replay_provider_and_benchmark():
    patch = propose(ReplayProvider(capacity_patch().model_dump_json()),
                    "capacity is now 6", initial_model())
    assert patch == capacity_patch()
    rows = evaluate()["rows"]
    assert len(rows) == 9
    rejected = [r for r in rows if r["method"] == "validated-patch-replay"
                and r["case"] != "capacity"]
    assert all(not r["accepted"] for r in rejected)
