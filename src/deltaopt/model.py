"""Typed intermediate representation for a bounded integer production model."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Product(Record):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    processing_time: float = Field(gt=0)
    profit: float
    minimum: int = Field(ge=0)
    maximum: int = Field(ge=0)
    category: str

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum > self.maximum:
            raise ValueError("minimum exceeds maximum")
        return self


class Model(Record):
    capacity: float = Field(ge=0)
    products: list[Product] = Field(min_length=1)
    source: str = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self):
        if len({p.id for p in self.products}) != len(self.products):
            raise ValueError("duplicate product IDs")
        return self


class Replacement(Record):
    path: str
    old: int | float | str
    value: int | float | str


class GraphPatch(Record):
    base_version: int = Field(ge=1)
    source: str = Field(min_length=1)
    valid_from: int = Field(ge=0)
    operations: list[Replacement] = Field(min_length=1)
    kind: Literal["replace"] = "replace"
