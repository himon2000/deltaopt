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

The bridge exports a versioned vendor-neutral payload. To connect an actual
Semantica deployment, implement GraphSink.ingest against a pinned SDK version
and test roundtrip identity, timestamps, provenance and idempotent retries.
There is no inferred causal semantics and no external service call in v0.1.
