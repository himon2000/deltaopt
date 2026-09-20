"""Copy-on-write patches with an allowlist and optimistic preconditions."""
from .model import GraphPatch, Model

FIELDS = {"processing_time", "profit", "minimum", "maximum", "category"}


def apply(model: Model, patch: GraphPatch, version: int) -> Model:
    if patch.base_version != version:
        raise ValueError("stale base version")
    data = model.model_dump()
    seen = set()
    for op in patch.operations:
        if op.path in seen:
            raise ValueError("duplicate patch path")
        seen.add(op.path)
        parts = op.path.split("/")
        if parts == ["", "capacity"]:
            target, key = data, "capacity"
        elif len(parts) == 4 and parts[:2] == ["", "products"] and parts[3] in FIELDS:
            matches = [p for p in data["products"] if p["id"] == parts[2]]
            if not matches:
                raise ValueError("unknown product")
            target, key = matches[0], parts[3]
        else:
            raise ValueError("path not allowed")
        if target[key] != op.old:
            raise ValueError("precondition failed")
        target[key] = op.value
    return Model.model_validate(data)
