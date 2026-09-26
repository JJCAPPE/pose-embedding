"""Measured bounded retrieval capacity check; never a selection outcome."""

from __future__ import annotations

import math
import time

from pose_embed.benchmark.descriptors import (
    descriptor_summary,
    encode_retrieval,
    make_score_rows,
)
from pose_embed.benchmark.retrieval import evaluate_retrieval, method_retrieval_policy
from pose_embed.benchmark.runtime import digest

PROFILE_RETRIEVAL = {
    "partition": "development-validation.jsonl",
    "prefix_size": 128,
    "order": "manifest_order",
    "selection_eligible": False,
}


def measure_retrieval(model, dataset, records, device, batch_size, method, parameters):
    started = time.perf_counter()
    descriptors = encode_retrieval(model, dataset, device, batch_size)
    encoding_seconds = time.perf_counter() - started
    started = time.perf_counter()
    result = evaluate_retrieval(
        descriptors["embeddings"],
        descriptors["embeddings"],
        records,
        records,
        score_rows=make_score_rows(model, descriptors, descriptors),
        scoring_policy=method_retrieval_policy(method, parameters),
    )
    scoring_seconds = time.perf_counter() - started
    return {
        "contract": dict(PROFILE_RETRIEVAL),
        "sample_count": len(records),
        "sample_ids": result["query_sample_ids"],
        "query_order_sha256": result["query_order_sha256"],
        "gallery_order_sha256": result["gallery_order_sha256"],
        "exclusion_sha256": result["exclusion_sha256"],
        "policy": result["policy"],
        "descriptor_storage": descriptor_summary(descriptors),
        "encoding_seconds": encoding_seconds,
        "scoring_seconds": scoring_seconds,
    }


def validate_retrieval_profile(evidence, identity, spec, records=None):
    if (
        not isinstance(evidence, dict)
        or identity.get("profile_retrieval") != PROFILE_RETRIEVAL
        or evidence.get("contract") != PROFILE_RETRIEVAL
        or evidence.get("policy")
        != method_retrieval_policy(spec.method_id, spec.parameters)
        or "metrics" in evidence
    ):
        raise ValueError("profile must bind the common real retrieval capacity check")
    count = evidence.get("sample_count")
    sample_ids = evidence.get("sample_ids")
    if (
        type(count) is not int
        or not 1 <= count <= 128
        or not isinstance(sample_ids, list)
        or len(sample_ids) != count
        or len(set(sample_ids)) != count
    ):
        raise ValueError("retrieval profile sample count or identities are invalid")
    if records is not None and sample_ids != [row.sample_id for row in records[:128]]:
        raise ValueError(
            "retrieval profile differs from the declared validation prefix"
        )
    from pose_embed.data.ntu import parse_ntu_sample_id

    identities = [parse_ntu_sample_id(value) for value in sample_ids]
    exclusions = [
        {
            "sample_id": q.sample_id,
            "excluded": [
                g.sample_id for g in identities if g.performance_id == q.performance_id
            ],
        }
        for q in identities
    ]
    if (
        evidence.get("query_order_sha256") != digest(sample_ids)
        or evidence.get("gallery_order_sha256") != digest(sample_ids)
        or evidence.get("exclusion_sha256") != digest(exclusions)
        or any(
            type(evidence.get(key)) not in (int, float)
            or not math.isfinite(evidence[key])
            or evidence[key] <= 0
            for key in ("encoding_seconds", "scoring_seconds")
        )
    ):
        raise ValueError(
            "retrieval profile timing or pool/exclusion hashes are invalid"
        )
    storage = evidence.get("descriptor_storage", {})
    fields = {"embeddings": ([count, spec.embedding_dimension], "float32")}
    if spec.method_id == "diml":
        fields.update(
            local=([count, 16, spec.embedding_dimension], "float32"),
            local_mask=([count, 16], "bool"),
        )
    elif spec.method_id == "proxy_anchor_avsl":
        fields["cam_std"] = ([count, 3, 512], "float32")
    expected_fields = {
        name: {
            "shape": shape,
            "dtype": dtype,
            "bytes": math.prod(shape) * (1 if dtype == "bool" else 4),
        }
        for name, (shape, dtype) in fields.items()
    }
    total = sum(value["bytes"] for value in expected_fields.values())
    if storage != {
        "count": count,
        "fields": expected_fields,
        "total_bytes": total,
        "bytes_per_sample": total // count,
    }:
        raise ValueError("retrieval profile descriptor shapes/dtypes/bytes differ")
