"""Deterministic P×K physical batch plans shared across objectives."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterator, Sequence

from torch.utils.data import Sampler


class BalancedBatchSampler(Sampler[list[int]]):
    """Yield deterministic batches with P classes and K examples per class.

    Classes and per-class examples are reshuffled from the declared seed whenever
    a queue wraps. This sampler never substitutes gradient accumulation for a
    physical P×K batch.
    """

    def __init__(
        self,
        labels: Sequence[int],
        *,
        classes_per_batch: int,
        samples_per_class: int,
        seed: int,
        batches_per_epoch: int | None = None,
    ) -> None:
        if classes_per_batch < 2 or samples_per_class < 2:
            raise ValueError("P and K must both be at least 2")
        if samples_per_class % 2:
            raise ValueError("K must be even for the contextual objective")
        by_class: dict[int, list[int]] = defaultdict(list)
        for index, label in enumerate(labels):
            by_class[int(label)].append(index)
        if len(by_class) < classes_per_batch:
            raise ValueError("not enough represented classes for one P×K batch")
        too_small = sorted(
            label
            for label, indexes in by_class.items()
            if len(indexes) < samples_per_class
        )
        if too_small:
            raise ValueError(f"classes contain fewer than K samples: {too_small}")
        self.by_class = dict(sorted(by_class.items()))
        self.classes_per_batch = classes_per_batch
        self.samples_per_class = samples_per_class
        self.seed = seed
        default_batches = math.ceil(
            len(labels) / (classes_per_batch * samples_per_class)
        )
        self.batches_per_epoch = batches_per_epoch or default_batches
        if self.batches_per_epoch < 1:
            raise ValueError("batches_per_epoch must be positive")

    def __len__(self) -> int:
        return self.batches_per_epoch

    def __iter__(self) -> Iterator[list[int]]:
        rng = random.Random(self.seed)
        classes = list(self.by_class)
        rng.shuffle(classes)
        class_cursor = 0
        pools = {label: indexes.copy() for label, indexes in self.by_class.items()}
        cursors = {label: 0 for label in self.by_class}
        for pool in pools.values():
            rng.shuffle(pool)

        for _ in range(self.batches_per_epoch):
            selected_classes = [
                classes[(class_cursor + offset) % len(classes)]
                for offset in range(self.classes_per_batch)
            ]
            class_cursor = (class_cursor + self.classes_per_batch) % len(classes)
            batch: list[int] = []
            for label in selected_classes:
                pool = pools[label]
                cursor = cursors[label]
                selected = [
                    pool[(cursor + offset) % len(pool)]
                    for offset in range(self.samples_per_class)
                ]
                batch.extend(selected)
                cursors[label] = (cursor + self.samples_per_class) % len(pool)
            yield batch
