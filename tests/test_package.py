import importlib


def test_package_imports():
    modules = [
        "ztf_classifier",
        "ztf_classifier.anomaly",
        "ztf_classifier.features",
        "ztf_classifier.io",
        "ztf_classifier.models",
        "ztf_classifier.preprocessing",
        "ztf_classifier.uncertainty",
        "ztf_classifier.visualization",
    ]

    for module_name in modules:
        module = importlib.import_module(module_name)
        assert module is not None
