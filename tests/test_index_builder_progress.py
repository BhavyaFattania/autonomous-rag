"""Tests for _insert_nodes_with_progress(), the batch-insert loop that gives
the indexer a real (done, total) completion percentage instead of an
indeterminate spinner."""

from src.indexer.index_builder import _insert_nodes_with_progress


class _FakeIndex:
    def __init__(self):
        self.batches: list[list[int]] = []

    def insert_nodes(self, nodes):
        self.batches.append(list(nodes))


def test_inserts_in_batches_and_reports_progress():
    index = _FakeIndex()
    nodes = list(range(150))
    calls: list[tuple[int, int]] = []

    _insert_nodes_with_progress(
        index, nodes, on_progress=lambda done, total: calls.append((done, total)), batch_size=64
    )

    assert [len(b) for b in index.batches] == [64, 64, 22]
    assert calls == [(64, 150), (128, 150), (150, 150)]


def test_empty_nodes_calls_neither_insert_nor_progress():
    index = _FakeIndex()
    calls: list[tuple[int, int]] = []

    _insert_nodes_with_progress(index, [], on_progress=calls.append)

    assert index.batches == []
    assert calls == []


def test_on_progress_is_optional():
    index = _FakeIndex()

    _insert_nodes_with_progress(index, [1, 2, 3], on_progress=None, batch_size=2)

    assert [len(b) for b in index.batches] == [2, 1]


def test_exact_multiple_of_batch_size_has_no_trailing_short_batch():
    index = _FakeIndex()
    calls: list[tuple[int, int]] = []

    _insert_nodes_with_progress(
        index,
        list(range(128)),
        on_progress=lambda done, total: calls.append((done, total)),
        batch_size=64,
    )

    assert [len(b) for b in index.batches] == [64, 64]
    assert calls == [(64, 128), (128, 128)]


def test_fewer_nodes_than_one_batch():
    index = _FakeIndex()
    calls: list[tuple[int, int]] = []

    _insert_nodes_with_progress(
        index, [1, 2, 3], on_progress=lambda done, total: calls.append((done, total)), batch_size=64
    )

    assert [len(b) for b in index.batches] == [3]
    assert calls == [(3, 3)]
