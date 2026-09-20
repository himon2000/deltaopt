import pytest
from rdflib import OWL, RDF, RDFS, SH, BNode, Literal, URIRef
from rdflib.compare import isomorphic

from deltaopt.contract import OntologyContract
from deltaopt.demo import capacity_patch, initial_model
from deltaopt.graph import OPT
from deltaopt.temporal import Store


def minimum_capacity_contract(tmp_path):
    contract = OntologyContract()
    contract.save(tmp_path)
    ontology = contract.ontology
    resource_type = URIRef("urn:test:BoundedResource")
    ontology.add((resource_type, RDF.type, OWL.Class))
    ontology.add((OPT.Parameter, RDFS.subClassOf, resource_type))
    ontology.serialize(tmp_path / "optimization.owl", format="xml")
    shapes = contract.shapes
    shape, prop = URIRef("urn:test:CapacityRule"), BNode()
    shapes.add((shape, RDF.type, SH.NodeShape))
    shapes.add((shape, SH.targetClass, resource_type))
    shapes.add((shape, SH.property, prop))
    shapes.add((prop, SH.path, OPT.value))
    shapes.add((prop, SH.minInclusive, Literal(7)))
    shapes.serialize(tmp_path / "shapes.ttl", format="turtle")
    return OntologyContract(tmp_path / "optimization.owl", tmp_path / "shapes.ttl")


def test_protege_rdfxml_roundtrip(tmp_path):
    original = OntologyContract()
    original.save(tmp_path)
    loaded = OntologyContract(tmp_path / "optimization.owl", tmp_path / "shapes.ttl")
    assert isomorphic(original.ontology, loaded.ontology)
    assert loaded.ontology_hash == original.ontology_hash
    assert loaded.shapes_hash == original.shapes_hash
    assert loaded.verify(initial_model())[0]


def test_edited_contract_controls_commit(tmp_path):
    contract = minimum_capacity_contract(tmp_path)
    store = Store(initial_model(), semantic_verifier=contract.verify)
    with pytest.raises(ValueError, match="semantic rejection"):
        store.commit(capacity_patch(), recorded_at=2)
    assert store.head.number == 1
    assert store.head.model.capacity == 8


def test_imports_require_local_merge(tmp_path):
    contract = OntologyContract()
    graph = contract.ontology
    graph.add((URIRef("urn:test"), OWL.imports, URIRef("https://example.org/external.owl")))
    path = tmp_path / "import.ttl"
    graph.serialize(path, format="turtle")
    with pytest.raises(ValueError, match="locally"):
        OntologyContract(path)


def test_contract_graph_cannot_be_mutated_externally():
    contract = OntologyContract()
    contract.ontology.remove((None, None, None))
    assert len(contract.ontology) > 0
