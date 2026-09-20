"""Solve max profit with integer quantities and one capacity constraint."""
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from .model import Model


@dataclass(frozen=True)
class SolverResult:
    status: str
    objective: float | None
    quantities: dict[str, int]


def verify(model: Model) -> SolverResult:
    products = model.products
    result = milp(
        c=-np.array([p.profit for p in products]),
        integrality=np.ones(len(products)),
        bounds=Bounds([p.minimum for p in products], [p.maximum for p in products]),
        constraints=LinearConstraint(
            [[p.processing_time for p in products]], -np.inf, model.capacity
        ),
        options={"time_limit": 10.0},
    )
    if result.status != 0:
        return SolverResult("infeasible" if result.status == 2 else "unknown", None, {})
    quantities = {p.id: round(x) for p, x in zip(products, result.x)}
    if any(abs(x - round(x)) > 1e-6 for x in result.x):
        return SolverResult("unknown", None, {})
    used = sum(p.processing_time * quantities[p.id] for p in products)
    if used > model.capacity + 1e-6 or any(
        not p.minimum <= quantities[p.id] <= p.maximum for p in products
    ):
        return SolverResult("unknown", None, {})
    return SolverResult("optimal", sum(p.profit * quantities[p.id] for p in products), quantities)
