# Benchmark scaffolding

Run `deltaopt evaluate` for nine method/case rows. All proposals are deterministic
replay. The full-regeneration mock serializes the complete candidate, patch-only
uses local operations with solver acceptance, and validated-patch additionally
gates on SHACL. Identical candidates deliberately isolate validation behavior;
they are not realistic generation baselines or evidence of LLM quality.

Cases: legal capacity decrease, unknown product category, infeasible required
demand. Extend with independently labeled update sequences before drawing
research conclusions. Planned JSONL fields:

```json
{"sequence_id":"production-001","step":1,"requirement":"capacity becomes 6h","gold_edit_paths":["/capacity"],"expected_status":"optimal","expected_objective":10.0}
```

Store real-provider results separately from replay and record model/provider,
sampling parameters, prompts, responses, token usage, versions and random seeds.
