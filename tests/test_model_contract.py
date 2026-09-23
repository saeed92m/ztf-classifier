from ztf_classifier.models.classes import (
    CLASS_TO_INDEX,
    MODEL_CLASSES,
    NUM_CLASSES,
)
from ztf_classifier.models.contracts import DEFAULT_MODEL_CONTRACT


def test_frozen_class_order() -> None:
    assert NUM_CLASSES == 15
    assert MODEL_CLASSES == (
        "AGN",
        "Blazar",
        "CEP",
        "CV/Nova",
        "DSCT",
        "E",
        "LPV",
        "Periodic-Other",
        "QSO",
        "RRL",
        "SLSN",
        "SNII",
        "SNIa",
        "SNIbc",
        "YSO",
    )
    assert CLASS_TO_INDEX["AGN"] == 0
    assert CLASS_TO_INDEX["YSO"] == 14


def test_frozen_xgboost_configuration() -> None:
    config = DEFAULT_MODEL_CONTRACT.config.xgboost

    assert config.n_estimators == 300
    assert config.max_depth == 4
    assert config.learning_rate == 0.05
    assert config.subsample == 0.85
    assert config.colsample_bytree == 0.85
    assert config.min_child_weight == 2
    assert config.reg_alpha == 0.0
    assert config.reg_lambda == 1.0
    assert config.objective == "multi:softprob"
    assert config.num_class == 15
    assert config.eval_metric == "mlogloss"
    assert config.tree_method == "hist"
    assert config.random_state == 42
    assert config.n_jobs == 4


def test_frozen_cross_validation_configuration() -> None:
    config = DEFAULT_MODEL_CONTRACT.config.cross_validation

    assert config.n_splits == 5
    assert config.shuffle is True
    assert config.random_state == 42


def test_frozen_calibration_configuration() -> None:
    config = DEFAULT_MODEL_CONTRACT.config.calibration

    assert config.method == "temperature_scaling"
    assert config.epsilon == 1e-12
    assert config.lower_bound == 0.05
    assert config.upper_bound == 10.0
    assert config.objective == "multiclass_log_loss"
    assert config.optimization_method == "bounded_scalar_minimization"


def test_frozen_conformal_configuration() -> None:
    config = DEFAULT_MODEL_CONTRACT.config.conformal

    assert config.method == "split_conformal_ood_diagnostic"
    assert config.alphas == (0.05, 0.10, 0.20)


def test_frozen_ood_configuration() -> None:
    config = DEFAULT_MODEL_CONTRACT.config.ood

    assert config.method == "IsolationForest"
    assert config.n_estimators == 300
    assert config.contamination == "auto"
    assert config.random_state == 42
    assert config.n_jobs == 4
    assert config.anomaly_thresholds == (90.0, 95.0, 99.0)


def test_contract_serialization() -> None:
    payload = DEFAULT_MODEL_CONTRACT.to_dict()

    assert payload["model_version"] == "baseline_v0.2"
    assert payload["model_family"] == "XGBoost"
    assert payload["classes"] == list(MODEL_CLASSES)
    assert payload["xgboost"]["num_class"] == NUM_CLASSES
    assert payload["missing_value_strategy"] == "native_xgboost_nan"
    assert payload["hyperparameter_tuning"] is False
