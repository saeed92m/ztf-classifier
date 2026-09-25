# Unified Scientific Feature Engine v0.1

The Scientific Feature Engine is the product boundary for deriving scientific features from normalized observations. The ML model consumes feature vectors, but feature generation is no longer treated as a permanent 42-column dataset implementation detail.

Each backend receives a normalized observation DataFrame and explicit parameters and returns a deterministic feature vector. Every result records the feature schema version, backend identity, backend software version, parameters, and SHA-256 of the normalized input observation table.

The initial `native` backend preserves the frozen v0.2 42-feature contract by delegating to the existing production-tested extractor. A future SCoPe-compatible backend can implement the same interface without making SCoPe a mandatory runtime dependency.

Scientific invariants: the v0.2 feature schema remains unchanged; feature order remains deterministic; observations are normalized before extraction; backend and parameters are explicit in provenance; feature computation is independent of HTTP/UI layers; synthetic observations are not introduced by the engine.


## Extensible backend registration

The engine supports explicit runtime backend registration through ScientificFeatureEngine.register_backend(). Each backend must declare:

- a unique name;
- software_version;
- feature_schema_version;
- a callable extract(observations, parameters=...) implementation.

Backend collisions are rejected unless replacement is explicitly requested. Backend metadata can be enumerated without executing feature extraction, allowing API and Workbench discovery.

The native v0.2 backend remains the default and its 42-feature contract is unchanged. New backends can expose new versioned feature schemas without changing the frozen native contract.
