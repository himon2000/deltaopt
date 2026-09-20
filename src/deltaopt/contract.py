"""An offline, immutable-by-copy ontology/SHACL contract edited with Protégé."""
import hashlib
from importlib.resources import files
from pathlib import Path

from owlrl import DeductiveClosure, RDFS_Semantics
from pyshacl import validate
from rdflib import OWL, RDF, SH, Graph
from rdflib.compare import to_canonical_graph

from .graph import to_rdf


class TermPreservingRDFS(RDFS_Semantics):
    def one_time_rules(self):
        # SHACL validates RDF terms, not numeric value equivalence. Do not
        # substitute 2.0^^double for 2^^integer in domain/range materialization.
        pass


def digest(graph):
    lines = sorted(" ".join(term.n3() for term in triple) for triple in to_canonical_graph(graph))
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


class OntologyContract:
    def __init__(self, ontology=None, shapes=None):
        resources = files("deltaopt").joinpath("resources")
        self._ontology = self._load(ontology, resources.joinpath("optimization.ttl"))
        self._shapes = self._load(shapes, resources.joinpath("shapes.ttl"))
        if not list(self._ontology.subjects(RDF.type, OWL.Ontology)):
            raise ValueError("ontology must declare owl:Ontology")
        if not list(self._shapes.subjects(RDF.type, SH.NodeShape)):
            raise ValueError("shapes must declare sh:NodeShape")
        # Imports are deliberately not dereferenced in the offline workflow.
        if list(self._ontology.triples((None, OWL.imports, None))):
            raise ValueError("merge imported ontologies locally before loading this contract")
        self.ontology_hash = digest(self._ontology)
        self.shapes_hash = digest(self._shapes)

    @staticmethod
    def _load(path, default):
        if path is None:
            return Graph().parse(data=default.read_text(), format="turtle")
        path = Path(path)
        formats = {".ttl": "turtle", ".owl": "xml", ".rdf": "xml", ".xml": "xml"}
        if path.suffix.lower() not in formats:
            raise ValueError("use a local .ttl or RDF/XML .owl/.rdf file")
        return Graph().parse(data=path.read_bytes(), format=formats[path.suffix.lower()])

    @property
    def ontology(self):
        return self._ontology + Graph()

    @property
    def shapes(self):
        return self._shapes + Graph()

    def materialize(self, model):
        graph = to_rdf(model) + self.ontology
        DeductiveClosure(TermPreservingRDFS).expand(graph)
        return graph

    def verify(self, model):
        conforms, _, report = validate(self.materialize(model), shacl_graph=self.shapes,
                                      inference="none", meta_shacl=True)
        return bool(conforms), str(report)

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.ontology.serialize(directory / "optimization.ttl", format="turtle")
        self.ontology.serialize(directory / "optimization.owl", format="xml")
        self.shapes.serialize(directory / "shapes.ttl", format="turtle")
