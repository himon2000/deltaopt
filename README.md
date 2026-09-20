# deltaopt

**Ontology-Constrained Temporal Graph Agents for Evolving Optimization Models**

Deltaopt is a small, executable research prototype for applying natural-language model changes as validated graph patches. Its vertical slice uses production planning: a plant has capacity and products have demand bounds, processing time, category, and cost.

## What actually works

- strict Pydantic `GraphPatch` protocol, optimistic version checks, preconditions, allow-listed replacement paths, atomic rollback;
- Protégé-openable OWL/Turtle ontology and the SHACL shapes actually loaded at runtime;
- separate valid time and recorded time, append-only versions, historical snapshots, source chains, and declared-dependency impact tracing;
- semantic verification via `pyshacl` and optimization verification via SciPy `milp`;
- deterministic offline replay for legal, semantic-invalid, feasible-invalid, and late-revision cases;
- isolated OpenAI-compatible provider interface (not called by demo/tests);
- runnable mock evaluation interfaces for full regeneration, patch-only, and ontology-constrained temporal patches;
- tests and GitHub Actions CI.

No Semantica runtime code is integrated. See [reuse boundary](docs/PROVENANCE.md). Dependency impact is not causal inference. Solver verification proves properties of the encoded model only; it does not automatically verify that natural-language intent was captured correctly.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
deltaopt demo
deltaopt evaluate
pytest
```

The demo needs no API key. It prints an explicit `offline deterministic replay` label. To build a real-model experiment, instantiate `OpenAICompatibleProvider`; credentials are read only from `DELTAOPT_API_KEY`, and real runs must be reported separately from replay.

## Expected demo behavior

1. capacity increase: accepted, SHACL-valid, MILP-feasible;
2. unknown category: rejected by SHACL even though the numeric model could solve;
3. excessive required demand: SHACL-valid but rejected as MILP-infeasible;
4. late correction: accepted, invisible in an earlier recorded-time snapshot and visible later;
5. rejected candidates leave model version/state unchanged.

## Evaluation scaffolding

`deltaopt evaluate` uses the same fixture data for all methods and reports semantic valid rate inputs, feasibility, constraint preservation, patch scope, traceability completeness, character-count proxies, and elapsed time. Current baseline generation is deterministic replay simulation, **not a real LLM experiment**. Full-regeneration expands the candidate to all leaf fields; the other methods emit local patches. See [research questions](docs/RESEARCH.md) and [architecture](docs/ARCHITECTURE.md).

## Layout

- `src/deltaopt/`: runtime, agent/provider boundary, validators, MILP, demo, evaluation
- `ontology/deltaopt.ttl`: OWL ontology
- `ontology/shapes/production.shacl.ttl`: runtime SHACL constraints
- `fixtures/`: offline replay and initial model
- `tests/`: end-to-end and safety behavior
- `docs/`: architecture, hypotheses, audited reuse/source record

## Limits / next research steps

- single-plant, single-capacity production model; no setup times, calendars, uncertainty, or multi-objective optimization;
- event replay has one valid-from boundary per patch rather than full interval supersession/conflict resolution;
- no real-provider benchmark, human intent labels, statistical claims, or paper results;
- OWL reasoning is not enabled; operational constraints are SHACL plus typed Python schema;
- no Semantica adapter; upstream compatibility is not claimed;
- provider output extraction assumes clean JSON and should gain hardened JSON-mode/tool-call adapters for production.

## License

MIT. The independent project's license is in `LICENSE`; upstream audit details and attribution boundary are documented separately.
