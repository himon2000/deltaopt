# Research plan

## Question

Can ontology-constrained localized repair reduce semantic regression and
unnecessary edits over long sequences of changing optimization requirements?

## Falsifiable hypotheses

1. With identical model, prompt budget and solver feedback, SHACL constraints
   reduce accepted semantic errors compared with patch-only repair.
2. Dependency localization reduces unnecessary edits compared with regeneration
   without lowering feasible-and-intent-correct solve rate.
3. Temporal provenance helps identify stale requirements after delayed changes.

## Planned comparison

Compare full regeneration, plain self-correction, structured IR generation and
temporal graph-guided patches. Ablate SHACL, localization, temporal provenance
and (future) repair memory separately. Use the same sequences, budgets, model
versions and seeded repeats. Split by problem family to prevent template leakage.

Start with capacity, demand, objective, resource and policy updates, including
contradictions and late corrections. Independently label the required change,
allowed edit set, unchanged requirements and feasible set. Use tiny exhaustively
enumerable cases as numerical oracles before expanding problem scale.

## Metrics to implement for real experiments

- Semantic regression rate: previously satisfied labeled requirements broken
  after an accepted update / previously satisfied requirements.
- Unnecessary edit rate: changed fields outside the gold edit set / changed fields
  (report zero with an explicit no-edit flag when denominator is zero).
- Provenance accuracy: changed facts linked to the correct gold source / changed facts.
- Executability, feasibility, objective correctness and intent correctness separately.
- Sequence survival length, rejection/retry counts, actual token cost and latency.

Current `deltaopt evaluate` only reports candidate SHACL validity, solver status,
acceptance, changed-field count, character-count proxy and elapsed time on three
deterministic smoke cases. It does not implement these research metrics in full
and supplies no empirical LLM claim. Report confidence intervals and failure
cases only after collecting real repeated experiments with held-out labels.

## Milestones

v0.1: runnable offline vertical slice (this repository).
Next: durable provenance, complete temporal semantics and audited native Semantica
adapter; add/remove IR operations; provider integration and held-out sequences;
then baseline experiments, ablations, repair memory and research report.
