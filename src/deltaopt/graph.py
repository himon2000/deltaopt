"""RDF projection and explicit dependency impact (not causal inference)."""
from rdflib import RDF, XSD, Graph, Literal, Namespace

from .model import Model

OPT = Namespace("https://w3id.org/deltaopt#")
DATA = Namespace("https://w3id.org/deltaopt/data/")


def to_rdf(model: Model) -> Graph:
    g = Graph()
    g.bind("opt", OPT)
    problem, requirement = DATA.problem, DATA.requirement
    g.add((requirement, RDF.type, OPT.Requirement))
    g.add((requirement, OPT.text, Literal(model.source)))
    g.add((problem, RDF.type, OPT.OptimizationProblem))
    g.add((problem, OPT.hasObjective, DATA.objective))
    g.add((DATA.objective, RDF.type, OPT.Objective))
    g.add((DATA.objective, OPT.sense, Literal("maximize")))
    g.add((DATA.objective, OPT.derivedFrom, requirement))
    g.add((DATA.param_capacity, RDF.type, OPT.Parameter))
    g.add((DATA.param_capacity, OPT.value, Literal(model.capacity, datatype=XSD.double)))
    g.add((DATA.capacity_constraint, RDF.type, OPT.CapacityConstraint))
    g.add((DATA.capacity_constraint, RDF.type, OPT.Constraint))
    g.add((DATA.capacity_constraint, OPT.usesParameter, DATA.param_capacity))
    g.add((DATA.capacity_constraint, OPT.derivedFrom, requirement))
    for p in model.products:
        node = DATA[p.id]
        g.add((node, RDF.type, OPT.DecisionVariable))
        g.add((node, OPT.belongsTo, problem))
        g.add((node, OPT.domain, Literal("integer")))
        g.add((node, OPT.category, Literal(p.category)))
        for key in ("processing_time", "profit", "minimum", "maximum"):
            g.add((node, OPT[key], Literal(getattr(p, key))))
        g.add((node, OPT.derivedFrom, requirement))
        g.add((DATA.objective, OPT.usesVariable, node))
        g.add((DATA.capacity_constraint, OPT.usesVariable, node))
    return g


def impact(model: Model, paths: list[str]) -> list[str]:
    """Return dependency closure for allowed IR field paths."""
    result = set(paths)
    for path in paths:
        if path == "/capacity":
            result.update(["capacity_constraint", "solution", "objective"])
        elif path.startswith("/products/"):
            product = path.split("/")[2]
            result.update([product, "solution", "objective"])
            if path.endswith("/processing_time"):
                result.add("capacity_constraint")
    return sorted(result)
