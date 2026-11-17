"""Continuation boundaries; the full numerical path is covered by the rehearsal."""

import json
from itertools import product
from types import SimpleNamespace

import pytest

from pose_embed import report
from pose_embed.artifacts import sidecar_path_for
from pose_embed.provenance import sha256_file
from pose_embed.validation_proofs import check_numerical_proof, validation_session


class CompleteMatrixReached(Exception):
    pass


@pytest.fixture
def split_inputs(tmp_path, monkeypatch):
    def file(name, content=None):
        path = tmp_path / name
        path.write_text(content or name)
        return path

    protocol = file("protocol.json")
    source = file("validator.py")
    direct = file("direct-input.json")
    base = file("base.npz")
    feature = file("feature.npz")
    base_sidecar = file(sidecar_path_for(base).name)
    feature_sidecar = file(sidecar_path_for(feature).name)
    sidecars = {
        base: SimpleNamespace(
            artifact_sha256=sha256_file(base),
            base_artifact_sha256=None,
            scientific_use_allowed=False,
            provenance={"inputs": {str(direct): sha256_file(direct)}},
        ),
        feature: SimpleNamespace(
            artifact_sha256=sha256_file(feature),
            base_artifact_sha256=sha256_file(base),
            scientific_use_allowed=False,
            provenance={
                "inputs": {
                    str(base): sha256_file(base),
                    str(base_sidecar): sha256_file(base_sidecar),
                }
            },
        ),
    }
    scientific = SimpleNamespace(
        protocol_lock=file("lock.json"),
        evaluation_plan=file("plan.json"),
        final_run_set=file("runs.json"),
        test_opening_ledger=file("opening.json"),
    )
    plan = SimpleNamespace(
        expected_rows=180,
        methods=("contrastive", "supcon", "contextual"),
        seeds=(7, 17, 29),
        conditions=tuple(f"condition-{index}" for index in range(10)),
        query_definitions=("primary", "official"),
    )
    keys = set(
        product(plan.methods, plan.seeds, plan.conditions, plan.query_definitions)
    )
    results = {}
    for index, (method, seed, condition, definition) in enumerate(sorted(keys)):
        path = file(f"result-{index:03d}.json")
        results[path] = SimpleNamespace(
            method=method,
            seed=seed,
            condition=condition,
            query_definition=definition,
            mode="final",
            protocol_sha256="a" * 64,
            gallery_artifact_sha256=sha256_file(feature),
            query_artifact_sha256=sha256_file(feature),
            gallery_sample_order_sha256="b" * 64,
            query_sample_order_sha256="c" * 64,
            metrics=SimpleNamespace(top1=1.0, mrr=1.0, r_at_5=1.0, query_count=20),
            provenance=SimpleNamespace(
                inputs={
                    str(feature): sha256_file(feature),
                    str(feature_sidecar): sha256_file(feature_sidecar),
                }
            ),
        )
    monkeypatch.setattr(
        report, "load_protocol", lambda _: SimpleNamespace(schema_version=3)
    )
    monkeypatch.setattr(report, "resolve_scientific_paths", lambda _: scientific)
    monkeypatch.setattr(report, "load_evaluation_plan", lambda _: plan)
    monkeypatch.setattr(report, "verify_protocol", lambda *a, **k: (None, "a" * 64))
    monkeypatch.setattr(report, "_load_result", lambda path: results[path])
    monkeypatch.setattr(report, "load_feature_sidecar", lambda path: sidecars[path])
    monkeypatch.setattr(report, "_report_split_source_paths", lambda: [source])
    monkeypatch.setattr(report, "proof_source_bindings", lambda *a, **k: {})
    monkeypatch.setattr(report, "numerical_runtime", lambda: {"threads": 1})
    calls = []

    def validate(rows, *, recompute_metrics, _lineages, **kwargs):
        calls.append((len(rows), recompute_metrics))
        _lineages.update(
            encoder=["encoder", "upstream", "preprocessing"],
            gallery=["gallery", "gallery-sidecar"],
            queries=[
                [condition, definition, "base", "sidecar"]
                for condition, definition in sorted(
                    {(row.condition, row.query_definition) for row in rows}
                )
            ],
        )
        return 180, keys

    monkeypatch.setattr(report, "_validate_final_provenance", validate)

    def aggregate(rows, index, **kwargs):
        assert len(rows) == len(index) == 180
        raise CompleteMatrixReached

    monkeypatch.setattr(report, "_core_report_artifacts", aggregate)
    summary = file(
        "summary.json",
        json.dumps(
            {
                "schema_version": 5,
                "analysis_scope": "core_confirmatory",
                "protocol_sha256": "a" * 64,
                "matrix": {
                    "observed_rows": 180,
                    "expected_rows": 180,
                    "complete": True,
                },
                **dict.fromkeys(
                    (
                        "primary_analysis",
                        "curve_data",
                        "error_analysis",
                        "telemetry",
                        "failures",
                    )
                ),
                "figures": [],
                "results": [
                    report._result_row(path, row) for path, row in results.items()
                ],
            }
        ),
    )
    return SimpleNamespace(
        protocol=protocol,
        paths=list(results),
        results=results,
        source=source,
        direct=direct,
        base=base,
        feature=feature,
        base_sidecar=base_sidecar,
        feature_sidecar=feature_sidecar,
        scientific=scientific,
        plan=plan,
        summary=summary,
        calls=calls,
        validate=validate,
        continuation=tmp_path / "continuation.json",
        output=tmp_path / "report",
    )


def start(inputs, role="construction"):
    if role == "construction":
        return report.build_report_part_one(
            inputs.paths, inputs.continuation, protocol_path=inputs.protocol
        )
    return report.validate_core_report_summary_part_one(
        inputs.summary, inputs.continuation, protocol_path=inputs.protocol
    )


def finish(inputs, receipt, role="construction"):
    options = {
        "continuation_path": inputs.continuation,
        "continuation_sha256": receipt["continuation_sha256"],
    }
    if role == "construction":
        return report.build_report(
            inputs.paths, inputs.output, protocol_path=inputs.protocol, **options
        )
    return report.validate_core_report_summary(
        inputs.summary, inputs.protocol, **options
    )


@pytest.mark.parametrize("role", ["construction", "independent_validation"])
def test_fixed_partition_reaches_only_complete_matrix(split_inputs, role):
    inputs = split_inputs
    receipt = start(inputs, role)
    assert receipt["complete"] is False
    assert not inputs.output.exists()
    payload = json.loads(inputs.continuation.read_text())
    assert len(payload["context"]["result_index"]) == 180
    assert len(payload["context"]["completed_keys"]) == 108
    assert payload["context"]["bound_bytes_per_recheck"] == sum(
        value["bytes"] for value in payload["context"]["bindings"].values()
    )
    with pytest.raises(CompleteMatrixReached):
        finish(inputs, receipt, role)
    numerical = role == "independent_validation"
    assert inputs.calls == [(108, numerical), (72, numerical)]


@pytest.mark.parametrize(
    "mutation",
    [
        "result",
        "base",
        "feature",
        "base_sidecar",
        "feature_sidecar",
        "direct",
        "source",
        "protocol",
        "opening",
        "runtime",
        "source_inventory",
        "retarget",
    ],
)
def test_continuation_rejects_changed_dependencies(split_inputs, monkeypatch, mutation):
    inputs = split_inputs
    receipt = start(inputs)
    if mutation == "runtime":
        monkeypatch.setattr(report, "numerical_runtime", lambda: {"threads": 2})
    elif mutation == "source_inventory":
        monkeypatch.setattr(
            report, "_report_split_source_paths", lambda: [inputs.source, inputs.direct]
        )
    elif mutation == "retarget":
        target = inputs.base.with_name("other-base.npz")
        target.write_bytes(inputs.base.read_bytes())
        inputs.base.unlink()
        inputs.base.symlink_to(target)
    else:
        path = (
            inputs.paths[-1]
            if mutation == "result"
            else inputs.scientific.test_opening_ledger
            if mutation == "opening"
            else getattr(inputs, mutation)
        )
        path.write_text("changed")
    with pytest.raises(ValueError, match="split report|report continuation"):
        finish(inputs, receipt)
    assert inputs.calls == [(108, False)]
    assert not inputs.output.exists()


@pytest.mark.parametrize(
    "mutation", ["role", "keys", "index", "partial", "hash", "lineages"]
)
def test_invalid_receipt_cannot_continue(split_inputs, mutation):
    inputs = split_inputs
    receipt = start(inputs)
    payload = json.loads(inputs.continuation.read_text())
    if mutation == "role":
        payload["context"]["role"] = "independent_validation"
    elif mutation == "keys":
        payload["context"]["completed_keys"].pop()
    elif mutation == "index":
        payload["context"]["result_index"].pop()
    elif mutation == "partial":
        payload.pop("lineages")
    elif mutation == "lineages":
        payload["lineages"] = None
    inputs.continuation.write_text(json.dumps(payload))
    if mutation != "hash":
        receipt["continuation_sha256"] = sha256_file(inputs.continuation)
    with pytest.raises(ValueError, match="report continuation"):
        finish(inputs, receipt)
    assert inputs.calls == [(108, False)]


@pytest.mark.parametrize("change", ["encoder", "gallery", "queries"])
def test_cross_partition_lineage_failure(split_inputs, monkeypatch, change):
    inputs = split_inputs
    receipt = start(inputs)

    def changed(rows, **kwargs):
        validated = inputs.validate(rows, **kwargs)
        if change == "queries":
            kwargs["_lineages"][change].pop()
        else:
            kwargs["_lineages"][change][0] = "different"
        return validated

    monkeypatch.setattr(report, "_validate_final_provenance", changed)
    with pytest.raises(ValueError, match="lineage"):
        finish(inputs, receipt)
    assert not inputs.output.exists()


@pytest.mark.parametrize("missing", ["cell", "duplicate", "mode"])
def test_part_one_cannot_record_incomplete_matrix(split_inputs, missing):
    inputs = split_inputs
    if missing == "cell":
        inputs.paths.pop()
    elif missing == "duplicate":
        inputs.paths[-1] = inputs.paths[0]
    else:
        inputs.results[inputs.paths[-1]].mode = "development"
    with pytest.raises(ValueError, match="exactly 180"):
        start(inputs)
    assert not inputs.continuation.exists()
    assert inputs.calls == []


def test_part_one_rechecks_before_immutable_write(split_inputs, monkeypatch):
    inputs = split_inputs

    def changed(rows, **kwargs):
        result = inputs.validate(rows, **kwargs)
        inputs.direct.write_text("changed during validation")
        return result

    monkeypatch.setattr(report, "_validate_final_provenance", changed)
    with pytest.raises(ValueError, match="bound input changed"):
        start(inputs)
    assert not inputs.continuation.exists()


def test_part_one_rejects_changed_result_between_load_and_binding(
    split_inputs, monkeypatch
):
    inputs = split_inputs
    reads = {}

    def load(path):
        reads[path] = reads.get(path, 0) + 1
        original = inputs.results[path]
        if reads[path] == 1:
            return original
        return SimpleNamespace(**{**vars(original), "protocol_sha256": "d" * 64})

    monkeypatch.setattr(report, "_load_result", load)
    with pytest.raises(ValueError, match="result changed while loading"):
        start(inputs)
    assert not inputs.continuation.exists()
    assert inputs.calls == []


def test_final_rechecks_first_partition_before_report_write(split_inputs, monkeypatch):
    inputs = split_inputs
    receipt = start(inputs)

    def aggregate(*args, **kwargs):
        inputs.direct.write_text("changed during aggregation")
        return {"json": {"primary-analysis.json": {}}, "text": {}, "references": {}}

    monkeypatch.setattr(report, "_core_report_artifacts", aggregate)
    with pytest.raises(ValueError, match="bound input changed"):
        finish(inputs, receipt)
    assert not (inputs.output / "summary.json").exists()


@pytest.mark.parametrize("entrypoint", ["construction", "independent_validation"])
def test_continuation_requires_external_digest_pair(split_inputs, entrypoint):
    inputs = split_inputs
    with pytest.raises(ValueError, match="supplied together"):
        if entrypoint == "construction":
            report.build_report(
                inputs.paths, inputs.output, continuation_path=inputs.continuation
            )
        else:
            report.validate_core_report_summary(
                inputs.summary, inputs.protocol, continuation_sha256="a" * 64
            )


def test_independent_first_part_never_inherits_numerical_proof(
    split_inputs, monkeypatch
):
    inputs = split_inputs
    checks = []

    def proof():
        check_numerical_proof(
            "split-isolation",
            enabled=True,
            files={str(inputs.direct): sha256_file(inputs.direct)},
            metadata={},
            check=lambda: checks.append(True),
        )

    def validate(rows, **kwargs):
        proof()
        return inputs.validate(rows, **kwargs)

    monkeypatch.setattr(report, "_validate_final_provenance", validate)
    with validation_session():
        proof()
        start(inputs, "independent_validation")
        proof()
    assert checks == [True, True]


def test_continuation_is_write_once(split_inputs):
    start(split_inputs)
    original = split_inputs.continuation.read_bytes()
    with pytest.raises((ValueError, FileExistsError)):
        start(split_inputs)
    assert split_inputs.continuation.read_bytes() == original


def test_source_bindings_are_collected_once_per_context(split_inputs, monkeypatch):
    inputs = split_inputs
    source = inputs.source.with_name("extra-source.py")
    source.write_text("bound by the active design")
    calls = []

    def bindings(protocol, *, scientific_use_allowed):
        calls.append(scientific_use_allowed)
        return {str(source): sha256_file(source)}

    monkeypatch.setattr(report, "proof_source_bindings", bindings)
    receipt = start(inputs)
    context = json.loads(inputs.continuation.read_text())["context"]
    assert context["bindings"][str(source)]["sha256"] == sha256_file(source)
    assert calls == [False]
    with pytest.raises(CompleteMatrixReached):
        finish(inputs, receipt)
    assert calls == [False, False]
