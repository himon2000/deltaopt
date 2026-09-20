"""Offline replay and an injected provider boundary; no network calls."""
from typing import Protocol

from .model import GraphPatch, Model


class PatchProvider(Protocol):
    def propose(self, requirement: str, model: dict, schema: dict) -> str: ...


def propose(provider: PatchProvider, requirement: str, model: Model) -> GraphPatch:
    return GraphPatch.model_validate_json(provider.propose(
        requirement, model.model_dump(), GraphPatch.model_json_schema()
    ))


class ReplayProvider:
    def __init__(self, response: str):
        self.response = response

    def propose(self, requirement: str, model: dict, schema: dict) -> str:
        return self.response
