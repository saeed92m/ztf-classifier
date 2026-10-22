import pytest

from scripts.diagnose_cpvs_sample import select_stratified_ids


def test_cpvs_sample_is_deterministic_balanced_and_nested():
    parent = set(range(1, 101))
    published = set(range(1, 51))

    sample_a, diagnostic_a = select_stratified_ids(
        parent, published, seed=1234, sample_size=20, diagnostic_size=10
    )
    sample_b, diagnostic_b = select_stratified_ids(
        parent, published, seed=1234, sample_size=20, diagnostic_size=10
    )

    assert sample_a == sample_b
    assert diagnostic_a == diagnostic_b
    assert len(sample_a) == 20
    assert sum(source_id in published for source_id in sample_a) == 10
    assert sum(source_id not in published for source_id in sample_a) == 10
    assert len(diagnostic_a) == 10
    assert sum(source_id in published for source_id in diagnostic_a) == 5
    assert sum(source_id not in published for source_id in diagnostic_a) == 5
    assert set(diagnostic_a).issubset(sample_a)


@pytest.mark.parametrize(
    "sample_size,diagnostic_size",
    [(0, 10), (11, 10), (20, 0), (20, 21), (20, 9)],
)
def test_cpvs_sample_rejects_invalid_sizes(sample_size, diagnostic_size):
    with pytest.raises(ValueError):
        select_stratified_ids(
            set(range(1, 101)),
            set(range(1, 51)),
            sample_size=sample_size,
            diagnostic_size=diagnostic_size,
        )
