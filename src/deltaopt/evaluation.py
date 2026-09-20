"""Smoke benchmark; deterministic candidates are not LLM baselines."""
from time import perf_counter

from .demo import capacity_patch, initial_model
from .model import GraphPatch
from .patch import apply
from .semantic import verify as semantic_verify
from .solver import verify as solver_verify


def evaluate():
    model = initial_model()
    rows = []
    for method in ["full-regeneration-replay", "patch-only-replay", "validated-patch-replay"]:
        for case, path, old, value in [
            ("capacity", "/capacity", 8.0, 6.0),
            ("invalid-category", "/products/A/category", "standard", "unknown"),
            ("infeasible-demand", "/products/A/minimum", 0, 4),
        ]:
            start = perf_counter()
            patch = capacity_patch().model_dump()
            patch["operations"] = [{"path": path, "old": old, "value": value}]
            if case == "infeasible-demand":
                patch["operations"].append({"path": "/products/B/minimum", "old": 0, "value": 1})
            candidate = apply(model, GraphPatch.model_validate(patch), 1)
            semantic_ok, _ = semantic_verify(candidate)
            solved = solver_verify(candidate)
            full = method == "full-regeneration-replay"
            accepted = solved.status == "optimal" and (
                semantic_ok if method == "validated-patch-replay" else True
            )
            rows.append({
                "method": method, "case": case,
                "semantic_valid": semantic_ok, "solver_status": solved.status,
                "accepted": accepted, "objective": solved.objective,
                "changed_fields": len(patch["operations"]),
                "proposal_characters": len(candidate.model_dump_json() if full else
                                           GraphPatch.model_validate(patch).model_dump_json()),
                "seconds": perf_counter() - start,
            })
    return {"mode": "deterministic smoke scaffolding, not comparative LLM evidence", "rows": rows}
