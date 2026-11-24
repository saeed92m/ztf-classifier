# Reconstructing a separately identified v0.2 model

## Scientific status

The original frozen production model binary has not been recovered. This procedure creates a new reconstruction, not the original model. It must not be copied or renamed into runs/model_baseline_v0.2_production/artifact/, and it is not production eligible until it passes the project's independent validation gates.

The procedure checks SHA-256 hashes for the four frozen inputs before training. It aborts on any mismatch. It uses the frozen 150-object dataset, 42-feature schema, fold assignments, class order, and model configuration. It trains out-of-fold models for temperature calibration, fits the final model on all 150 objects, writes a schema-1.0 artifact, reloads it, and checks exact prediction parity after reload.

## Run

From the repository root in the project's supported Python 3.11 environment:

    python scripts/rebuild_v0_2_model_reconstruction.py

The script writes to a new timestamped directory under runs/, for example:

    runs/reconstructed-baseline-v0.2-YYYYMMDDTHHMMSSZ/

It does not overwrite an existing directory. It refuses to write under the legacy production path. The output includes artifact/, OOF predictions, and reconstruction_record.json.

## Important limits

- This cannot establish byte-for-byte identity with the missing original model.
- The ALeRCE labels are benchmark labels, not independent ground truth.
- The reconstruction record sets production_eligible to false.
- The original production artifact remains a scientific validation blocker.
- Do not use the reconstruction for public classifications or claim that it restores the original v0.2.0 model.
