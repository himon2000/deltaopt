import json
import socket

import pytest
from rdflib import Graph
from rdflib.compare import isomorphic

pytest.importorskip("semantica", reason="optional pinned source checkout required")

from test_contract import minimum_capacity_contract

from deltaopt.contract import OntologyContract
from deltaopt.demo import capacity_patch, initial_model
from deltaopt.graph import to_rdf
from deltaopt.semantica_native import SemanticaRuntime
from deltaopt.temporal import Store


@pytest.fixture(autouse=True)
def forbid_network_and_provider(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline integration attempted network/provider creation")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    import semantica.ontology.llm_generator as generator
    monkeypatch.setattr(generator, "create_provider", forbidden)


def test_native_ingestion_and_validation():
    runtime = SemanticaRuntime()
    assert runtime.engine.llm.provider is None
    assert len(runtime.ontology_index["classes"]) >= 8
    assert runtime.verify(initial_model())[0]
    invalid = initial_model()
    invalid.products[0].category = "unknown"
    valid, report = runtime.verify(invalid)
    assert not valid
    assert json.loads(report)["violation_count"] >= 1


def test_native_custom_contract_is_enforced(tmp_path):
    runtime = SemanticaRuntime(minimum_capacity_contract(tmp_path))
    store = Store(initial_model(), semantic_verifier=runtime.verify)
    with pytest.raises(ValueError, match="semantic rejection"):
        store.commit(capacity_patch(), recorded_at=2)
    assert len(store.versions) == 1


def test_native_temporal_queries_and_rollback():
    runtime = SemanticaRuntime()
    store = Store(initial_model(), semantic_verifier=runtime.verify)
    store.commit(capacity_patch(valid_from=2), recorded_at=8)
    assert runtime.snapshot(store, valid_at=2, known_at=7).metadata["selected_version"] == 1
    assert runtime.snapshot(store, valid_at=2, known_at=8).metadata["selected_version"] == 2
    assert runtime.snapshot(store, valid_at=1, known_at=8).metadata["selected_version"] == 1
    store.rollback(1, valid_from=3, recorded_at=9, source="restore")
    graph = runtime.snapshot(store, valid_at=3, known_at=9)
    assert graph.metadata["selected_version"] == 3
    assert all(r["restored_from"] == 1 for r in graph.relationships)
    assert all(r["requirement_source"] == "restore" for r in graph.relationships)


def test_bundle_roundtrip_and_no_overwrite(tmp_path):
    runtime = SemanticaRuntime()
    store = Store(initial_model(), semantic_verifier=runtime.verify)
    store.commit(capacity_patch(), recorded_at=2)
    manifest = runtime.export_bundle(store, tmp_path)
    assert manifest["conforms"]
    assert manifest["versions"] == 2
    project = Graph().parse(tmp_path / "protege-project.owl", format="xml")
    assert isomorphic(project, runtime.contract.ontology + to_rdf(store.head.model))
    loaded = OntologyContract(tmp_path / "optimization.owl", tmp_path / "shapes.ttl")
    assert loaded.ontology_hash == runtime.contract.ontology_hash
    graph = json.loads((tmp_path / "semantica-graph.json").read_text())
    ids = {e["id"] for e in graph["entities"]}
    assert all(r["source"] in ids and r["target"] in ids for r in graph["relationships"])
    assert len({r["id"] for r in graph["relationships"]}) == len(graph["relationships"])
    with pytest.raises(ValueError, match="empty"):
        runtime.export_bundle(store, tmp_path)
