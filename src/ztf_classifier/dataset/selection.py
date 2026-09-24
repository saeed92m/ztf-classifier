"""Object-selection execution policies."""

from __future__ import annotations

import pandas as pd

from ztf_classifier.dataset.config import DatasetConfig
from ztf_classifier.dataset.manifest import REQUIRED_OBJECT_COLUMNS
from ztf_classifier.dataset.selector import ObjectSelectionRequest
from ztf_classifier.io.object_acquisition import ObjectAcquisitionBackend


class ObjectSelectionPolicy:
    """Execute deterministic object-selection strategies."""

    def __init__(self, config: DatasetConfig) -> None:
        self._config = config

    def acquire_class(
        self,
        *,
        class_name: str,
        backend: ObjectAcquisitionBackend,
    ) -> pd.DataFrame:
        """Acquire objects for one class using the configured strategy."""

        strategy = self._config.selection_strategy

        if strategy == "strict_primary":
            return self._acquire_at_probability(
                class_name=class_name,
                probability=self._config.probability_min,
                backend=backend,
            )

        if strategy == "fallback_on_empty":
            return self._acquire_with_fallback(
                class_name=class_name,
                backend=backend,
            )

        if strategy == "historical_full_requery":
            return self._acquire_at_probability(
                class_name=class_name,
                probability=self._config.fallback_probability
                if self._config.fallback_probability is not None
                else self._config.probability_min,
                backend=backend,
            )

        raise ValueError(
            "unsupported selection_strategy: "
            + strategy
        )

    def acquire_all(
        self,
        *,
        backend: ObjectAcquisitionBackend,
    ) -> pd.DataFrame:
        """Acquire and canonicalize objects for every configured class."""

        frames: list[pd.DataFrame] = []

        if self._config.selection_strategy == "historical_full_requery":
            self._run_historical_availability_check(backend=backend)

        for class_name in self._config.classes:
            frame = self.acquire_class(
                class_name=class_name,
                backend=backend,
            )

            if not frame.empty:
                frames.append(frame)

        if not frames:
            return pd.DataFrame(columns=tuple(REQUIRED_OBJECT_COLUMNS))

        combined = pd.concat(
            frames,
            axis=0,
            ignore_index=True,
        )

        if combined["oid"].duplicated().any():
            duplicates = sorted(
                combined.loc[
                    combined["oid"].duplicated(keep=False),
                    "oid",
                ].astype(str).unique()
            )
            raise ValueError(
                "Object selection produced duplicate OIDs: "
                + ", ".join(duplicates)
            )

        return combined.sort_values("oid").reset_index(drop=True)

    def _run_historical_availability_check(
        self,
        *,
        backend: ObjectAcquisitionBackend,
    ) -> None:
        """Perform the historical primary-threshold availability pass."""

        for class_name in self._config.classes:
            self._acquire_at_probability(
                class_name=class_name,
                probability=self._config.probability_min,
                backend=backend,
            )

    def _acquire_with_fallback(
        self,
        *,
        class_name: str,
        backend: ObjectAcquisitionBackend,
    ) -> pd.DataFrame:
        """Try primary threshold, then fallback only when empty."""

        primary = self._acquire_at_probability(
            class_name=class_name,
            probability=self._config.probability_min,
            backend=backend,
        )

        if not primary.empty:
            return primary

        fallback_probability = self._config.fallback_probability

        if fallback_probability is None:
            return primary

        return self._acquire_at_probability(
            class_name=class_name,
            probability=fallback_probability,
            backend=backend,
        )

    def _acquire_at_probability(
        self,
        *,
        class_name: str,
        probability: float,
        backend: ObjectAcquisitionBackend,
    ) -> pd.DataFrame:
        """Execute one acquisition request at one probability threshold."""

        request = ObjectSelectionRequest(
            survey=self._config.survey,
            classifier=self._config.classifier,
            class_name=class_name,
            probability=probability,
            page_size=self._config.effective_page_size,
            classifier_version=self._config.classifier_version,
        )

        result = backend.acquire(request)
        frame = self._extract_dataframe(result.objects)

        required = set(REQUIRED_OBJECT_COLUMNS)
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(
                "Object-acquisition backend returned non-canonical data; "
                "missing columns: "
                + ", ".join(missing)
            )

        if frame["class"].astype(str).ne(class_name).any():
            raise ValueError(
                f"Object-acquisition backend returned rows outside requested "
                f"class {class_name!r}."
            )

        probabilities = pd.to_numeric(
            frame["probability"],
            errors="coerce",
        )
        if probabilities.isna().any():
            raise ValueError(
                f"Object-acquisition backend returned invalid probabilities "
                f"for class {class_name!r}."
            )

        if (probabilities < probability).any():
            raise ValueError(
                f"Object-acquisition backend returned an object below the "
                f"requested probability threshold for class {class_name!r}."
            )

        return self._limit_samples(frame)

    @staticmethod
    def _extract_dataframe(
        objects: tuple[object, ...],
    ) -> pd.DataFrame:
        """Extract the single DataFrame returned by the backend."""

        if len(objects) != 1:
            raise ValueError(
                "Object-acquisition backend must return exactly one "
                "object payload per request."
            )

        payload = objects[0]

        if not isinstance(payload, pd.DataFrame):
            raise TypeError(
                "Object-acquisition backend payload must be a pandas "
                "DataFrame."
            )

        return payload

    def _limit_samples(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Limit a result to the configured samples per class."""

        return frame.sort_values(
            ["probability", "oid"],
            ascending=[False, True],
        ).head(
            self._config.samples_per_class
        ).reset_index(drop=True)
