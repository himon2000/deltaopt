"""Append-only, in-memory commit log. Rollbacks create new commits."""
from copy import deepcopy
from dataclasses import dataclass

from . import semantic, solver
from .model import GraphPatch, Model
from .patch import apply


@dataclass(frozen=True)
class Version:
    number: int
    parent: int | None
    valid_from: int
    recorded_at: int
    source: str
    model: Model
    patch: GraphPatch | None = None
    restored_from: int | None = None


class Store:
    def __init__(self, model: Model, *, semantic_verifier=None):
        self._semantic_verifier = semantic_verifier or semantic.verify
        self._check(model)
        self._versions = [Version(1, None, 0, 0, model.source, model.model_copy(deep=True))]

    def _check(self, model):
        ok, report = self._semantic_verifier(model)
        if not ok:
            raise ValueError("semantic rejection: " + report)
        if solver.verify(model).status != "optimal":
            raise ValueError("solver rejection: infeasible or unverified")

    @property
    def versions(self):
        return deepcopy(self._versions)

    @property
    def head(self):
        return deepcopy(self._versions[-1])

    def _clock(self, recorded_at):
        if type(recorded_at) is not int or recorded_at <= self.head.recorded_at:
            raise ValueError("recorded_at must strictly increase")

    def commit(self, patch: GraphPatch, recorded_at: int) -> Version:
        self._clock(recorded_at)
        candidate = apply(self.head.model, patch, self.head.number)
        self._check(candidate)
        self._versions.append(Version(
            self.head.number + 1, self.head.number, patch.valid_from, recorded_at,
            patch.source, candidate, patch.model_copy(deep=True)
        ))
        return self.head

    def snapshot(self, valid_at: int, known_at: int) -> Model:
        """Latest recorded eligible full snapshot; see documented temporal limits."""
        eligible = [v for v in self._versions
                    if v.valid_from <= valid_at and v.recorded_at <= known_at]
        if not eligible:
            raise ValueError("no snapshot at requested time")
        return eligible[-1].model.model_copy(deep=True)

    def rollback(self, version: int, *, valid_from: int, recorded_at: int, source: str):
        self._clock(recorded_at)
        if type(version) is not int or not 1 <= version <= len(self._versions):
            raise ValueError("unknown version")
        if type(valid_from) is not int or valid_from < 0 or not source.strip():
            raise ValueError("rollback needs valid time and source")
        model = self._versions[version - 1].model.model_copy(deep=True)
        self._check(model)
        self._versions.append(Version(
            self.head.number + 1, self.head.number, valid_from, recorded_at, source,
            model, restored_from=version
        ))
        return self.head
