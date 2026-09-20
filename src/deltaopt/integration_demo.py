"""Protégé-authored contract -> native Semantica -> validated patch -> export."""
from .contract import OntologyContract
from .demo import capacity_patch, initial_model
from .semantica_native import SemanticaRuntime
from .solver import verify
from .temporal import Store


def run(ontology=None, shapes=None, output=None):
    runtime = SemanticaRuntime(OntologyContract(ontology, shapes))
    store = Store(initial_model(), semantic_verifier=runtime.verify)
    before = verify(store.head.model).objective
    store.commit(capacity_patch(), recorded_at=2)
    after = verify(store.head.model).objective
    earlier = runtime.snapshot(store, valid_at=1, known_at=1)
    later = runtime.snapshot(store, valid_at=1, known_at=2)
    graph = runtime.knowledge_graph(store)
    result = {"mode": "native Semantica, offline, provider disabled",
              "objective": [before, after],
              "ontology_classes": len(runtime.ontology_index["classes"]),
              "entities": len(graph.entities), "relationships": len(graph.relationships),
              "known_before": earlier.metadata["selected_version"],
              "known_after": later.metadata["selected_version"],
              "ontology_hash": runtime.contract.ontology_hash}
    if output:
        result["bundle"] = runtime.export_bundle(store, output)
    return result
