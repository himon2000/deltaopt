# Architecture and verification boundary

The typed production model is the source of truth. RDF is regenerated from it
for SHACL and export; patch operations target stable product IDs rather than
array offsets. Only capacity and existing product attributes are editable.
Validation runs on an isolated candidate, then the temporal store appends a
commit. Any schema, precondition, semantic or solver error leaves history intact.

The solver maximizes sum(profit_i * quantity_i), with integer quantities bounded
by minimum_i/maximum_i and sum(time_i * quantity_i) <= capacity. Time is measured
in hours; there is no unit conversion. Only optimal results are committed;
timeouts and unknown outcomes are rejected along with infeasibility.

Every commit records its source, patch, parent, valid_from and recorded_at.
RDF retains the original model requirement; changed-field provenance is in the
patch log and bridge export, not a complete per-triple provenance graph.
Rollback copies a historical state into a new commit and records restored_from.
Callers receive defensive copies of history and snapshots.

Time values are nonnegative integer ticks. Recorded time strictly increases.
Historical queries choose the latest recorded full snapshot satisfying both
time bounds. This is a deliberately limited snapshot semantics, not a complete
bitemporal database: a later full snapshot can carry changes with unrelated
valid times. Do not use it for independent overlapping retroactive updates.

The original bridge exports a versioned vendor-neutral payload. The v0.2 native
adapter below handles the pinned in-memory Semantica integration. Connecting an
external persistent deployment through GraphSink.ingest remains future work,
including idempotent retries and durable storage.
There is no inferred causal semantics or external service call.

v0.2 adds an optional native adapter and a frozen-by-copy OntologyContract.
Store accepts a semantic verifier so custom ontology/SHACL constraints gate
both initial state and all later commits/rollbacks. The adapter materializes
RDFS classes/properties without replacing datatype-distinct numeric literals,
then uses native Semantica SHACL validation. Full RDF is preserved alongside
the upstream ontology index. See [integration guide](protege_semantica.md).
