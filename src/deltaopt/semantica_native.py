"""Offline adapter for the pinned cusz-semantic Semantica source tree."""
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from rdflib import BNode, Literal

from .contract import OntologyContract
from .graph import to_rdf

UPSTREAM_SHA = "8bb1803fc1d2da6c3056e88af2dd101f6c32829e"
EPOCH = datetime(2000, 1, 1, tzinfo=UTC)


def tick(value):
    """Map DeltaOpt's logical tick to an explicit UTC second for Semantica."""
    return EPOCH + timedelta(seconds=value)


class SemanticaRuntime:
    def __init__(self, contract=None):
        try:
            from semantica.ingest import OntologyIngestor
            from semantica.kg import BiTemporalFact, KnowledgeGraph, TemporalGraphQuery
            from semantica.ontology import OntologyEngine
        except ImportError as exc:
            raise RuntimeError("Semantica offline dependencies missing; see docs/protege_semantica.md") from exc
        self.contract = contract or OntologyContract()
        self._fact = BiTemporalFact
        self._graph = KnowledgeGraph
        self._query = TemporalGraphQuery(temporal_granularity="second")
        # Explicitly disable provider creation, including upstream's default OpenAI provider.
        self.engine = OntologyEngine(provider=None)
        with TemporaryDirectory(prefix="deltaopt-ontology-") as temporary:
            path = Path(temporary) / "ontology.ttl"
            self.contract.ontology.serialize(path, format="turtle")
            self.ontology_index = OntologyIngestor().ingest_ontology(path).data
        # Drop an ephemeral path; retain the complete RDF separately from this lossy index.
        self.ontology_index.get("metadata", {}).pop("source_path", None)

    def verify(self, model):
        # Check shape syntax too: upstream validate_graph does not enable meta-SHACL.
        self.contract.verify(model)
        report = self.engine.validate_graph(
            self.contract.materialize(model),
            shacl=self.contract.shapes.serialize(format="turtle"), explain=True,
        )
        return report.conforms, json.dumps(report.to_dict())

    def knowledge_graph(self, store):
        """One isolated RDF snapshot per commit, with native temporal fields."""
        entities, relationships = {}, []
        for version in store.versions:
            fields = self._fact(valid_from=tick(version.valid_from), valid_until=None,
                                recorded_at=tick(version.recorded_at)).to_relationship_fields()
            graph = to_rdf(version.model)
            for subject, predicate, obj in sorted(graph, key=lambda t: tuple(x.n3() for x in t)):
                ids = []
                for term in (subject, obj):
                    term_id = f"v{version.number}:" + hashlib.sha256(term.n3().encode()).hexdigest()
                    ids.append(term_id)
                    entities[term_id] = {
                        "id": term_id,
                        "type": "Literal" if isinstance(term, Literal) else
                                "BlankNode" if isinstance(term, BNode) else "Resource",
                        "rdf_term": term.n3(), "version": version.number, **fields,
                    }
                relationships.append({
                    "id": f"v{version.number}:" + hashlib.sha256(
                        " ".join(t.n3() for t in (subject, predicate, obj)).encode()
                    ).hexdigest(),
                    "source": ids[0], "target": ids[1], "type": str(predicate),
                    "version": version.number, "requirement_source": version.source,
                    "parent": version.parent, "restored_from": version.restored_from, **fields,
                })
        return self._graph(entities=list(entities.values()), relationships=relationships,
                           metadata={"ontology_hash": self.contract.ontology_hash,
                                     "shapes_hash": self.contract.shapes_hash,
                                     "semantics": "append-only version snapshots, not fact supersession",
                                     "tick_epoch": EPOCH.isoformat()})

    def snapshot(self, store, *, valid_at, known_at):
        graph = asdict(self.knowledge_graph(store))
        graph = self._query.reconstruct_at_time(graph, tick(valid_at), time_axis="valid")
        graph = self._query.reconstruct_at_time(graph, tick(known_at), time_axis="transaction")
        versions = {edge["version"] for edge in graph["relationships"]}
        if not versions:
            raise ValueError("no snapshot at requested time")
        latest = max(versions)
        return self._graph(
            entities=[e for e in graph["entities"] if e["version"] == latest],
            relationships=[e for e in graph["relationships"] if e["version"] == latest],
            metadata={**graph["metadata"], "selected_version": latest},
        )

    def export_bundle(self, store, directory):
        directory = Path(directory)
        if directory.exists() and any(directory.iterdir()):
            raise ValueError("choose an empty output directory to preserve existing artifacts")
        self.contract.save(directory)
        to_rdf(store.head.model).serialize(directory / "model.ttl", format="turtle")
        (self.contract.ontology + to_rdf(store.head.model)).serialize(
            directory / "protege-project.owl", format="xml")
        data = asdict(self.knowledge_graph(store))
        (directory / "semantica-graph.json").write_text(json.dumps(data, indent=2))
        from .semantica_bridge import export
        history = export(store)
        history["integration"] = "native Semantica offline ontology, validation and KG adapter"
        (directory / "history.json").write_text(json.dumps(history, indent=2))
        ok, report = self.verify(store.head.model)
        manifest = {"ontology_hash": self.contract.ontology_hash,
                    "shapes_hash": self.contract.shapes_hash, "conforms": ok,
                    "tested_upstream_commit": UPSTREAM_SHA,
                    "native_report": json.loads(report), "versions": len(store.versions)}
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return manifest
