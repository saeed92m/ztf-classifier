# Model Findings

Model iterations follow this evidence chain:

previous model -> previous metrics -> new model -> benchmark -> calibration -> OOD -> failure analysis -> decision

A model is not accepted as improved solely because one metric increased. Relevant macro and per-class performance, probabilistic quality, OOD/rejection behavior, latency, reproducibility, and failure patterns must be considered.
