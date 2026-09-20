# DeltaOpt v0.2

**Ontology-Constrained Temporal Graph Agents for Evolving Optimization Models**

A runnable research prototype for changing an optimization model through small,
validated graph patches. The first domain is integer production planning:
maximize profit under one machine-capacity constraint and per-product bounds.

## Run locally

Requires Python 3.11 or newer. No API key or commercial solver is needed.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
deltaopt demo
deltaopt evaluate
pytest
```

The demo changes capacity from **8 to 6 hours**, patches only `/capacity`, and
solves the encoded MILP: the optimum changes from **13 to 10**. It then restores
the original model with an append-only rollback commit (objective **13**).
Products A/B have processing times 2/3, profits 3/5 and bounds 0–4/0–2.

## Protégé + native Semantica (offline)

v0.2 loads locally edited Turtle/RDF/XML ontologies and SHACL shapes, validates
patches through the actual Semantica engine from `cusz-semantic`, builds native
temporal knowledge graphs, and exports an OWL project for Protégé inspection.
No API key is needed; the model provider is explicitly disabled.

See [setup and editing guide](docs/protege_semantica.md) for the pinned source
checkout and `deltaopt semantic-demo --output artifacts/first-run` command.
Custom contract rules gate commits; tests cover a new ontology superclass plus
a SHACL capacity rule that rejects the 6h patch while accepting the initial 8h.

## Implemented

- Typed Python model and strict structured patch protocol; allowlisted paths,
  base-version checks, old-value preconditions, copy-on-write application.
- Optimization RDF graph with requirement provenance and dependency impact.
- Protégé-openable OWL vocabulary and runtime SHACL checks with `pyshacl`.
- SciPy/HiGHS integer optimization verifier with independent result checks.
- In-memory temporal commits, valid/recorded timestamps, historical snapshots,
  rejected-candidate isolation, and rollback as a new version.
- Offline replay agent plus an injected provider protocol.
- Semantica bridge export containing RDF, versions, provenance and patch records;
  a caller-supplied `GraphSink` can receive this payload.
- Executable baseline/evaluation scaffolding and regression tests.

## Architecture

```text
Requirement -> provider/replay -> structured patch -> impact localization
                                      |
                         schema + version + preconditions
                                      |
                            copy-on-write candidate
                                      |
                       RDF/SHACL -> MILP verification
                                      |
                            temporal commit / reject
                                      |
                         bridge export / history / rollback
```

## Project map

| Path | Purpose |
| --- | --- |
| `src/deltaopt/` | Model, RDF, patch, agent, verifier, temporal store, bridge, CLI |
| `ontology/optimization.ttl` | OWL vocabulary, opens in Protégé |
| `ontology/shapes.ttl` | Operational SHACL rules |
| `src/deltaopt/resources/` | Packaged copies of ontology assets, parity-tested |
| `tests/` | Positive, negative, solver, temporal, bridge and replay coverage |
| `benchmarks/` | Smoke benchmark instructions and planned dataset contract |
| `docs/` | Research plan, architecture and provenance boundaries |

## Research status and limits

This is **offline deterministic replay**, not a trained or evaluated LLM agent.
`PatchProvider` is an interface; no real LLM provider is configured or called.
Full regeneration and patch-only evaluation use deterministic candidates, so
their outputs are infrastructure checks, not evidence of method superiority.

The original Semantica bridge remains a vendor-neutral export contract. The
optional v0.2 adapter uses native ontology, validation, KG and temporal APIs;
it does not run Semantica's web application or persistent graph database.
Dependency tracing is not causal inference.
SHACL checks the projected structure and selected domain rules; it does not
prove correspondence with arbitrary natural-language requirements. The solver
verifies the encoded model only. OWL DL consistency checking is not implemented.

Temporal snapshots, including the native adapter, select the latest recorded eligible full-state commit.
This supports the demo's late correction, but not general interval supersession
or merging independent retroactive changes. State is in memory; durable storage,
multiwriter concurrency, add/remove graph operations and repair memory remain
future work. See [architecture](docs/architecture.md) and
[research plan](docs/research_plan.md).

## Provenance

This completion implements the scope recovered from the prior conversation and
the existing repository scaffold. The prior conversation's downloadable source
archive was not available, so byte-for-byte recovery of that archive is not
claimed. Existing MIT licensing is retained. Native integration imports the
pinned `cusz-semantic` checkout without copying or modifying its source;
see [reuse boundary](docs/provenance.md).
