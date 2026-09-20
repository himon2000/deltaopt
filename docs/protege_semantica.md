# Protégé + Semantica offline workflow

DeltaOpt v0.2 connects locally edited ontology files to the actual Semantica
classes from `himon2000/cusz-semantic`, audited at commit
`8bb1803fc1d2da6c3056e88af2dd101f6c32829e` (backend version 0.6.5).
It does not run a model API, embedding service, Neo4j server or web backend.

## Setup

From the DeltaOpt repository with the virtual environment activated:

```bash
python -m pip install -e '.[dev,semantica]'
git clone https://github.com/himon2000/cusz-semantic.git ../cusz-semantic
git -C ../cusz-semantic checkout 8bb1803fc1d2da6c3056e88af2dd101f6c32829e
export PYTHONPATH="$(cd ../cusz-semantic/backend && pwd)${PYTHONPATH:+:$PYTHONPATH}"
deltaopt semantic-demo --output artifacts/first-run
pytest
```

The `semantica` extra installs the additional lightweight dependencies, not the
entire Semantica distribution. The pinned checkout on PYTHONPATH supplies the
real upstream modules. This avoids installing unrelated NLP/LLM dependencies
declared by its full backend package. Other Semantica versions are not certified.
The original repository is only read, never edited by DeltaOpt.

## Edit in Protégé

1. Open `artifacts/first-run/protege-project.owl` in Protégé to inspect ontology
   classes, properties and the final production-model individuals together.
2. For schema changes, open `ontology/optimization.ttl` (or the exported
   `optimization.owl`) and save a separate `.ttl` or RDF/XML `.owl` file. Keep
   existing DeltaOpt IRIs stable. Turtle saved with `.owl` should instead use `.ttl`.
3. Edit SHACL in a text editor (or a suitable SHACL plugin). Protégé OWL axioms
   and SHACL closed-world constraints have different roles. OWL restrictions
   are not automatically converted into SHACL constraints.
4. Load the saved files explicitly:

```bash
deltaopt semantic-demo --ontology edited/optimization.owl \
  --shapes edited/shapes.ttl --output artifacts/edited-run
```

For an observable rule change, add a superclass `BoundedResource` to `Parameter`
in Protégé. Add a SHACL node shape targeting `BoundedResource`, with property
`opt:value sh:minInclusive 7`. The initial 8h model passes; the 6h patch is rejected
and no new version is committed. Automated tests exercise this exact pattern.

An exported instance graph is for inspection, not an unrestricted edit-to-solver
import: runtime quantities/parameters still come from the typed optimization IR.
Changes to IRIs or solver semantics require corresponding Python changes.
Merge imported ontologies locally; the loader rejects `owl:imports` instead of
fetching remote resources. Only local Turtle and RDF/XML input is supported.

## Native calls and data ownership

- `OntologyIngestor.ingest_ontology`: indexes classes/properties from the contract.
- `OntologyEngine(provider=None).validate_graph`: returns native SHACL reports.
- `KnowledgeGraph`: contains entities and relationships from RDF snapshots.
- `BiTemporalFact`: serializes valid and recorded timestamps on graph elements.
- `TemporalGraphQuery.reconstruct_at_time`: filters both time axes; DeltaOpt
  chooses the latest eligible version to match its existing snapshot semantics.

RDFS subclass/property inference is materialized before native validation.
Numeric literal substitution is disabled so integer and double RDF terms retain
their SHACL datatypes. This is not OWL DL reasoning or automatic translation of
all OWL restrictions. The complete source RDF is retained because Semantica's
ontology dictionary is an index and does not losslessly represent every axiom.

Every version's graph has isolated IDs, source information and logical ticks
mapped to UTC seconds since 2000-01-01. These are demonstration logical times,
not claims about actual event dates. Snapshot graphs remain append-only; full
per-fact interval supersession is future work. Rollback creates a new version.

## Export bundle

`optimization.ttl` and `optimization.owl` preserve the contract RDF;
`shapes.ttl` preserves operational rules; `model.ttl` contains final instances;
`protege-project.owl` combines ontology and instances; `semantica-graph.json`
contains native KG data; `history.json` retains patches and provenance;
`manifest.json` records content hashes, native SHACL report and tested upstream SHA.
Blank-node-canonicalized hashes survive Turtle/RDF/XML roundtrips.

Use an empty output directory. The integration tests block socket connections
and provider creation, verify changed-rule rejection, temporal selection,
rollback, graph endpoint integrity and RDF roundtrips. They skip only when
Semantica is absent; the dedicated CI job supplies the pinned checkout.
