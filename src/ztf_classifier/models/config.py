"""Frozen v0.2 ML configuration contracts."""

from __future__ import annotations

from dataclasses import dataclass

from ztf_classifier.models.classes import NUM_CLASSES


@dataclass(frozen=True)
class XGBoostConfig:
    n_estimators: int = 300
    max_depth: int = 4
    learning_rate: float = 0.05
    subsample: float = 0.85
    colsample_bytree: float = 0.85
    min_child_weight: int = 2
    reg_alpha: float = 0.0
    reg_lambda: float = 1.0
    objective: str = "multi:softprob"
    num_class: int = NUM_CLASSES
    eval_metric: str = "mlogloss"
    tree_method: str = "hist"
    random_state: int = 42
    n_jobs: int = 4

    def __post_init__(self) -> None:
        if self.n_estimators <= 0:
            raise ValueError("n_estimators must be positive.")
        if self.max_depth <= 0:
            raise ValueError("max_depth must be positive.")
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive.")
        if not 0 < self.subsample <= 1:
            raise ValueError("subsample must be in (0, 1].")
        if not 0 < self.colsample_bytree <= 1:
            raise ValueError("colsample_bytree must be in (0, 1].")
        if self.min_child_weight < 0:
            raise ValueError("min_child_weight must be non-negative.")
        if self.reg_alpha < 0:
            raise ValueError("reg_alpha must be non-negative.")
        if self.reg_lambda < 0:
            raise ValueError("reg_lambda must be non-negative.")
        if self.objective != "multi:softprob":
            raise ValueError("Frozen v0.2 objective must be multi:softprob.")
        if self.num_class != NUM_CLASSES:
            raise ValueError("num_class must equal the frozen class count.")
        if self.eval_metric != "mlogloss":
            raise ValueError("Frozen v0.2 eval_metric must be mlogloss.")
        if self.tree_method != "hist":
            raise ValueError("Frozen v0.2 tree_method must be hist.")
        if self.n_jobs <= 0:
            raise ValueError("n_jobs must be positive.")


@dataclass(frozen=True)
class CrossValidationConfig:
    n_splits: int = 5
    shuffle: bool = True
    random_state: int = 42

    def __post_init__(self) -> None:
        if self.n_splits < 2:
            raise ValueError("n_splits must be at least 2.")


@dataclass(frozen=True)
class CalibrationConfig:
    method: str = "temperature_scaling"
    epsilon: float = 1e-12
    lower_bound: float = 0.05
    upper_bound: float = 10.0
    objective: str = "multiclass_log_loss"
    optimization_method: str = "bounded_scalar_minimization"

    def __post_init__(self) -> None:
        if self.method != "temperature_scaling":
            raise ValueError("Frozen calibration method is temperature_scaling.")
        if self.epsilon <= 0:
            raise ValueError("epsilon must be positive.")
        if not 0 < self.lower_bound < self.upper_bound:
            raise ValueError("Invalid temperature bounds.")


@dataclass(frozen=True)
class ConformalConfig:
    method: str = "split_conformal_ood_diagnostic"
    alphas: tuple[float, ...] = (0.05, 0.10, 0.20)

    def __post_init__(self) -> None:
        if not self.alphas:
            raise ValueError("At least one conformal alpha is required.")
        if any(not 0 < alpha < 1 for alpha in self.alphas):
            raise ValueError("Conformal alpha values must be in (0, 1).")


@dataclass(frozen=True)
class OODConfig:
    method: str = "IsolationForest"
    n_estimators: int = 300
    contamination: str = "auto"
    random_state: int = 42
    n_jobs: int = 4
    anomaly_thresholds: tuple[float, ...] = (90.0, 95.0, 99.0)

    def __post_init__(self) -> None:
        if self.n_estimators <= 0:
            raise ValueError("n_estimators must be positive.")
        if self.contamination != "auto":
            raise ValueError("Frozen v0.2 contamination must be auto.")
        if self.n_jobs <= 0:
            raise ValueError("n_jobs must be positive.")
        if any(not 0 <= value <= 100 for value in self.anomaly_thresholds):
            raise ValueError("OOD thresholds must be percentages in [0, 100].")


@dataclass(frozen=True)
class ModelConfig:
    version: str = "baseline_v0.2"
    family: str = "XGBoost"
    xgboost: XGBoostConfig = XGBoostConfig()
    cross_validation: CrossValidationConfig = CrossValidationConfig()
    calibration: CalibrationConfig = CalibrationConfig()
    conformal: ConformalConfig = ConformalConfig()
    ood: OODConfig = OODConfig()
    missing_value_strategy: str = "native_xgboost_nan"
    hyperparameter_tuning: bool = False

    def __post_init__(self) -> None:
        if self.version != "baseline_v0.2":
            raise ValueError("Frozen model version must be baseline_v0.2.")
        if self.family != "XGBoost":
            raise ValueError("Frozen model family must be XGBoost.")
        if self.missing_value_strategy != "native_xgboost_nan":
            raise ValueError(
                "Frozen missing-value strategy must be native_xgboost_nan."
            )
        if self.hyperparameter_tuning:
            raise ValueError("Frozen v0.2 does not use hyperparameter tuning.")
