"""Runtime SHACL validation over the RDF projection."""
from importlib.resources import files

from pyshacl import validate
from rdflib import Graph

from .graph import to_rdf
from .model import Model


def verify(model: Model) -> tuple[bool, str]:
    resource = files("deltaopt").joinpath("resources")
    shapes = Graph().parse(data=resource.joinpath("shapes.ttl").read_text(), format="turtle")
    ontology = Graph().parse(
        data=resource.joinpath("optimization.ttl").read_text(), format="turtle"
    )
    conforms, _, report = validate(
        to_rdf(model), shacl_graph=shapes, ont_graph=ontology, inference="rdfs"
    )
    return bool(conforms), str(report)
