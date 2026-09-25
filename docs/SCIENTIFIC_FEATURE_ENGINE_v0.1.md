# Unified Scientific Feature Engine v0.1

The Scientific Feature Engine is the product boundary for deriving scientific features from normalized observations. The ML model consumes feature vectors, but feature generation is no longer treated as a permanent 42-column dataset implementation detail.

Each backend receives a normalized observation DataFrame and explicit parameters and returns a deterministic feature vector. Every result records the feature schema version, backend identity, backend software version, parameters, and SHA-256 of the normalized input observation table.

The initial `native` backend preserves the frozen v0.2 42-feature contract by delegating to the existing production-tested extractor. A future SCoPe-compatible backend can implement the same interface without making SCoPe a mandatory runtime dependency.

Scientific invariants: the v0.2 feature schema remains unchanged; feature order remains deterministic; observations are normalized before extraction; backend and parameters are explicit in provenance; feature computation is independent of HTTP/UI layers; synthetic observations are not introduced by the engine.
