# Provenance and reuse boundary

Conceptual context: https://github.com/himon2000/cusz-semantic and the project
conversation proposing Protégé/OWL/SHACL plus temporal graph-guided repair.
No upstream source is copied. v0.2 audits and integration-tests commit
`8bb1803fc1d2da6c3056e88af2dd101f6c32829e`, backend version 0.6.5 (MIT,
Copyright 2026 Hawksight AI). Its original license remains in the separate checkout.
The adapter calls OntologyIngestor, OntologyEngine, KnowledgeGraph,
BiTemporalFact and TemporalGraphQuery through their public interfaces.
Compatibility beyond this pinned source revision is not asserted.
The repository is an independent implementation and keeps
the existing MIT license. Dependencies retain their respective licenses.

The original referenced conversation exposes descriptions and demo results but
no recoverable source attachment. This implementation recreates the requested
v0.1 scope; it is not presented as a byte-identical upload of an unavailable zip.

The namespace https://w3id.org/deltaopt is a vocabulary identifier only; no
registration or hosted ontology resolution is claimed.
