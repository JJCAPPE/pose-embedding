"""Batch-first retrieval descriptors shared by cosine and structural scorers."""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import DataLoader

from pose_embed.benchmark.retrieval import CUSTOM_SCORERS


def encode_retrieval(model, dataset, device, batch_size: int) -> dict[str, np.ndarray]:
    was_training = model.training
    model.eval()
    chunks: dict[str, list[np.ndarray]] = {}
    try:
        with torch.inference_mode():
            for poses, _ in DataLoader(dataset, batch_size=batch_size, shuffle=False):
                values = (
                    model.retrieval_descriptors(poses.to(device))
                    if hasattr(model, "retrieval_descriptors")
                    else {"embeddings": model(poses.to(device))}
                )
                if not isinstance(values, dict) or "embeddings" not in values:
                    raise ValueError("retrieval requires an embeddings descriptor")
                if chunks and set(values) != set(chunks):
                    raise ValueError(
                        "retrieval descriptor keys changed between batches"
                    )
                for name, value in values.items():
                    if (
                        not isinstance(name, str)
                        or not name.isidentifier()
                        or not isinstance(value, torch.Tensor)
                        or value.ndim < 1
                        or value.shape[0] != len(poses)
                        or not torch.isfinite(value).all()
                    ):
                        raise ValueError(
                            "model produced invalid batch-first retrieval descriptors"
                        )
                    chunks.setdefault(name, []).append(value.detach().cpu().numpy())
    finally:
        model.train(was_training)
    if not chunks:
        raise ValueError("retrieval dataset must not be empty")
    return {name: np.concatenate(parts) for name, parts in chunks.items()}


def descriptor_summary(descriptors: dict[str, np.ndarray]) -> dict:
    if "embeddings" not in descriptors or not descriptors["embeddings"].shape[0]:
        raise ValueError("descriptor summary requires nonempty embeddings")
    count = descriptors["embeddings"].shape[0]
    fields = {}
    for name, values in descriptors.items():
        if values.ndim < 1 or values.shape[0] != count or not np.isfinite(values).all():
            raise ValueError("retrieval descriptors are not aligned finite arrays")
        fields[name] = {
            "shape": list(values.shape),
            "dtype": str(values.dtype),
            "bytes": values.nbytes,
        }
    total = sum(row["bytes"] for row in fields.values())
    return {
        "count": count,
        "fields": fields,
        "total_bytes": total,
        "bytes_per_sample": total // count,
    }


def make_score_rows(model, query_descriptors, gallery_descriptors):
    method_id = getattr(model, "method_id", "contrastive")
    if method_id not in CUSTOM_SCORERS:
        return None
    factory = getattr(model.head, "make_retrieval_scorer", None)
    if factory is None:
        raise ValueError("declared structural retrieval has no implemented scorer")
    return factory(query_descriptors, gallery_descriptors)


def validate_descriptors(descriptors, method_id, count, dimension):
    summary = descriptor_summary(descriptors)
    expected = {"embeddings": (count, dimension)}
    if method_id == "diml":
        expected.update(local=(count, 16, dimension), local_mask=(count, 16))
    elif method_id == "proxy_anchor_avsl":
        expected["cam_std"] = (count, 3, 512)
    if set(descriptors) != set(expected) or any(
        descriptors[name].shape != shape for name, shape in expected.items()
    ):
        raise ValueError("retrieval descriptor fields/shapes differ from method recipe")
    for name, values in descriptors.items():
        if name == "local_mask":
            if values.dtype != np.bool_:
                raise ValueError("local descriptor validity must be boolean")
        elif not np.issubdtype(values.dtype, np.floating):
            raise ValueError("retrieval descriptors must be floating point")
    return summary


def save_descriptors(directory, descriptors, method_id, dimension):
    from pose_embed.provenance import write_immutable_json

    summary = validate_descriptors(
        descriptors, method_id, len(descriptors["embeddings"]), dimension
    )
    with (directory / "retrieval-descriptors.npz").open("xb") as stream:
        np.savez(stream, **descriptors)
    write_immutable_json(directory / "descriptor-storage.json", summary)


def read_descriptors(directory, method_id, count, dimension):
    from pose_embed.benchmark.runtime import read_json

    with np.load(
        directory / "retrieval-descriptors.npz", allow_pickle=False
    ) as archive:
        descriptors = {name: archive[name] for name in archive.files}
    summary = validate_descriptors(descriptors, method_id, count, dimension)
    if summary != read_json(directory / "descriptor-storage.json"):
        raise ValueError("descriptor storage metadata differs from saved arrays")
    return descriptors
