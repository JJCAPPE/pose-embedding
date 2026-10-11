"""Measured campaign admission and clean-only, immutable v3 selection."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from pose_embed.config import ExperimentConfig, StrictModel, load_experiment
from pose_embed.config_v3 import SHA256, ArtifactBinding, ProtocolV3Config
from pose_embed.protocol import protocol_digest, resolve_scientific_paths
from pose_embed.protocol_v3 import (
    V3SelectionAuthorization,
    _bound_file,
    _timestamp,
    require_v3_design,
)
from pose_embed.provenance import sha256_file, write_immutable_json

Method = Literal["contrastive", "supcon", "contextual"]
CONDITIONS = (
    "coordinate_jitter:0.01",
    "coordinate_jitter:0.025",
    "coordinate_jitter:0.05",
    "joint_mask:3",
    "joint_mask:6",
    "joint_mask:8",
    "frame_mask:10",
    "frame_mask:25",
    "frame_mask:40",
)
ANALYSIS_CHECKS = {
    "full_command_rehearsal",
    "exact_180_cells",
    "missing_duplicate_rejection",
    "ordered_subset_equality",
    "v3_report_dispatch",
    "unequal_view_bootstrap",
    "interpretation_identity",
    "tamper_revision_rejection",
    "preloader_authorization",
    "concurrent_crashed_opening_recovery",
    "cross_version_training_denial",
    "real_opening_unchanged",
    "successor_cache_independent_validation",
    "successor_pilot_independent_validation",
}
GEOMETRY_CHECKS = {
    "panel_frozen_before_scores",
    "two_fresh_processes_exact",
    "invariants_passed",
    "full_query_damage_telemetry",
    "fixed_original_fallback",
    "nine_encodings_reused",
}


class AdmissionReceipt(StrictModel):
    schema_version: Literal[1]
    protocol_sha256: SHA256
    design_lock_sha256: SHA256
    recorded_at: datetime
    recorded_by: str = Field(min_length=1, pattern=r"\S")
    scientific_use_allowed: Literal[True]
    status: Literal["passed"]
    evidence: tuple[ArtifactBinding, ...] = Field(min_length=1)
    code_sha256: dict[str, SHA256]


class CorruptionReceipt(AdmissionReceipt):
    query_count: Literal[18929]
    query_sample_order_sha256: SHA256
    checks: dict[str, Literal[True]]
    encodings: dict[str, ArtifactBinding]
    results: tuple[ArtifactBinding, ...] = Field(min_length=27, max_length=27)
    geometry_panel: ArtifactBinding


class AnalysisReceipt(AdmissionReceipt):
    checks: dict[str, Literal[True]]
    development_dependence_table: ArtifactBinding
    novel_metadata_dependence_table: ArtifactBinding


class ResearcherAvailability(StrictModel):
    recorded_at: datetime
    recorded_by: str = Field(min_length=1, pattern=r"\S")
    source: str = Field(min_length=1, pattern=r"\S")
    normal_weekly_hours: float = Field(gt=0, allow_inf_nan=False)
    contingency_weekly_hours: float = Field(ge=0, allow_inf_nan=False)
    guaranteed_weekly_hours: dict[date, float]
    contingency_weeks: tuple[date, ...] = ()

    @model_validator(mode="after")
    def conservative_hours(self):
        import math

        _timestamp(self.recorded_at)
        if (
            not self.guaranteed_weekly_hours
            or any(
                day.weekday() != 0
                or not math.isfinite(hours)
                or not 0
                <= hours
                <= max(self.normal_weekly_hours, self.contingency_weekly_hours)
                for day, hours in self.guaranteed_weekly_hours.items()
            )
            or set(self.contingency_weeks)
            != {
                day
                for day, hours in self.guaranteed_weekly_hours.items()
                if hours > self.normal_weekly_hours
            }
            or len(set(self.contingency_weeks)) != len(self.contingency_weeks)
        ):
            raise ValueError(
                "availability must explicitly identify authorized contingency weeks"
            )
        return self


class AllocationWindow(StrictModel):
    starts_at: datetime
    ends_at: datetime
    job_wall_limit_seconds: int = Field(gt=0)
    queue_allowance_seconds: int = Field(ge=0)
    concurrent_scientific_processes: Literal[1]

    @model_validator(mode="after")
    def usable_window(self):
        if (
            self.starts_at.tzinfo is None
            or self.ends_at.tzinfo is None
            or (self.ends_at - self.starts_at).total_seconds()
            <= self.queue_allowance_seconds
        ):
            raise ValueError(
                "allocation calendar requires positive timezone-aware windows"
            )
        return self


class AllocationCalendar(StrictModel):
    recorded_at: datetime
    recorded_by: str = Field(min_length=1, pattern=r"\S")
    access: Literal["ordinary_queued_access"]
    reserved: Literal[False]
    windows: tuple[AllocationWindow, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def sequential_windows(self):
        _timestamp(self.recorded_at)
        windows = sorted(self.windows, key=lambda window: window.starts_at)
        if any(
            left.ends_at > right.starts_at
            for left, right in zip(windows, windows[1:], strict=False)
        ):
            raise ValueError("allocation windows cannot overlap")
        return self


class CapacityReceipt(AdmissionReceipt):
    filesystem_free_bytes: int = Field(ge=0)
    quota_remaining_bytes: int = Field(ge=0)
    remaining_peak_bytes: int = Field(ge=0)
    compute_slack: float = Field(ge=1.25, allow_inf_nan=False)
    researcher_slack: float = Field(ge=1.25, allow_inf_nan=False)
    allocation_calendar: ArtifactBinding
    researcher_availability: ArtifactBinding
    final_lock_date: date
    novel_completion_date: date
    measured_stage_seconds: dict[str, float]
    peak_host_bytes: int = Field(gt=0)
    peak_gpu_bytes: int = Field(gt=0)
    host_memory_limit_bytes: int = Field(gt=0)
    gpu_memory_limit_bytes: int = Field(gt=0)
    maximum_job_seconds: float = Field(gt=0, allow_inf_nan=False)
    retained_bytes: int = Field(gt=0)
    full_size_resident_rows: Literal[95001]
    timing_optimization_actions: Literal[80]
    remaining_preopening_seconds: float = Field(gt=0, allow_inf_nan=False)
    remaining_evaluation_seconds: float = Field(gt=0, allow_inf_nan=False)
    researcher_work_hours: dict[str, float]

    @model_validator(mode="after")
    def feasible(self) -> CapacityReceipt:
        import math

        if (
            self.peak_host_bytes > self.host_memory_limit_bytes
            or self.peak_gpu_bytes > self.gpu_memory_limit_bytes
        ):
            raise ValueError("measured peak memory exceeds the allocation")
        if min(self.filesystem_free_bytes, self.quota_remaining_bytes) < (
            200 * 2**30 + 1.25 * self.remaining_peak_bytes
        ):
            raise ValueError("campaign storage reserve is insufficient")
        if self.final_lock_date > date(2026, 11, 29) or (
            self.novel_completion_date > date(2026, 12, 6)
            or self.novel_completion_date < self.final_lock_date
        ):
            raise ValueError("campaign forecast misses the protected deadlines")
        stages = {
            "hashing",
            "loading",
            "preprocessing",
            "encoding",
            "projection",
            "artifact_validation",
            "retrieval",
            "serialization",
            "final_resident_training",
        }
        if set(self.measured_stage_seconds) != stages or any(
            not math.isfinite(value) or value <= 0
            for value in self.measured_stage_seconds.values()
        ):
            raise ValueError("capacity requires every measured full-pipeline stage")
        packages = {
            "implementation_review",
            "release_revalidation",
            "corruption_audit",
            "analysis_report_verification",
            "resource_planning",
            "selection_final_supervision",
            "final_analysis_delivery",
        }
        if set(self.researcher_work_hours) != packages or any(
            not math.isfinite(hours) or hours < 0
            for hours in self.researcher_work_hours.values()
        ):
            raise ValueError(
                "capacity requires separate measured researcher work packages"
            )
        return self


class SealReceipt(AdmissionReceipt):
    artifact_root_registry_sha256: SHA256
    opening_records_absent: Literal[True]
    unresolved_roots: tuple[()] = ()


class MatrixSlot(StrictModel):
    method: Method
    learning_rate: Literal[0.0001, 0.0003, 0.001]
    seed: Literal[7, 17, 29]
    config: ArtifactBinding


class SelectionMatrix(StrictModel):
    schema_version: Literal[1]
    protocol_sha256: SHA256
    slots: tuple[MatrixSlot, ...] = Field(min_length=27, max_length=27)

    @model_validator(mode="after")
    def exact_matrix(self) -> SelectionMatrix:
        expected = {
            (m, r, s)
            for m in ("contrastive", "supcon", "contextual")
            for r in (0.0001, 0.0003, 0.001)
            for s in (7, 17, 29)
        }
        if {_slot_key(slot) for slot in self.slots} != expected:
            raise ValueError("selection requires the exact 27 unique matrix slots")
        return self


class SelectionAttempt(StrictModel):
    attempt: ArtifactBinding
    outcome: ArtifactBinding | None
    failure: (
        Literal["infrastructure", "numerical", "implementation", "unresolved"] | None
    )
    evidence: tuple[ArtifactBinding, ...] = ()
    retry_of: str | None = None
    remedy: ArtifactBinding | None = None


class CompletedSlot(StrictModel):
    method: Method
    learning_rate: Literal[0.0001, 0.0003, 0.001]
    seed: Literal[7, 17, 29]
    attempts: tuple[SelectionAttempt, ...] = Field(min_length=1)


class SelectionLedger(StrictModel):
    schema_version: Literal[1]
    protocol_sha256: SHA256
    run_matrix_sha256: SHA256
    slots: tuple[CompletedSlot, ...] = Field(min_length=27, max_length=27)


class SelectedConfigurations(StrictModel):
    schema_version: Literal[1]
    kind: Literal["v3_selected_configurations"]
    protocol_sha256: SHA256
    selection_authorization_sha256: SHA256
    recorded_at: datetime
    recorded_by: str = Field(min_length=1, pattern=r"\S")
    ledger: ArtifactBinding
    candidates: tuple[dict, ...]
    selected_rates: dict[Method, float]


def _slot_key(slot) -> tuple:
    return slot.method, slot.learning_rate, slot.seed


def _read(root: Path, binding: ArtifactBinding, model):
    return model.model_validate_json(_bound_file(root, binding).read_text())


def _campaign_binding(root, protocol, binding):
    path = _bound_file(root, binding)
    prefix = (
        root / Path(protocol.test_access.resolved_protocol_relative_path).parent.parent
    )
    if not path.is_relative_to(prefix):
        raise ValueError("campaign artifact belongs to a different execution revision")
    return path


def _receipt(root, binding, model, protocol, authorization):
    from pose_embed.protocol import current_code_hashes

    _campaign_binding(root, protocol, binding)
    receipt = _read(root, binding, model)
    _timestamp(receipt.recorded_at)
    if (
        receipt.protocol_sha256 != protocol_digest(protocol)
        or receipt.design_lock_sha256 != authorization.design_lock_sha256
        or receipt.recorded_at > authorization.recorded_at
        or receipt.code_sha256 != current_code_hashes().model_dump()
    ):
        raise ValueError("admission evidence has wrong protocol/design or chronology")
    for evidence in receipt.evidence:
        _bound_file(root, evidence)
    return receipt


def _validate_capacity_availability(root, capacity, *, as_of=None):
    from datetime import timedelta
    from zoneinfo import ZoneInfo

    project_timezone = ZoneInfo("America/New_York")
    as_of = capacity.recorded_at if as_of is None else as_of
    if as_of < capacity.recorded_at:
        raise ValueError("capacity cannot authorize work before its measurement")
    calendar = _read(root, capacity.allocation_calendar, AllocationCalendar)
    availability = _read(root, capacity.researcher_availability, ResearcherAvailability)
    if (
        calendar.recorded_at > capacity.recorded_at
        or availability.recorded_at > capacity.recorded_at
    ):
        raise ValueError("capacity predates its allocation or researcher evidence")
    preopening = 0.0
    evaluation = 0.0
    for window in calendar.windows:
        if window.starts_at < as_of:
            raise ValueError("remaining capacity cannot count a past allocation window")
        seconds = (
            window.ends_at - window.starts_at
        ).total_seconds() - window.queue_allowance_seconds
        if capacity.compute_slack * capacity.maximum_job_seconds > min(
            window.job_wall_limit_seconds, seconds
        ):
            raise ValueError(
                "complete measured jobs do not fit usable allocation windows "
                "and scheduler wall limits"
            )
        start_date = window.starts_at.astimezone(project_timezone).date()
        end_date = window.ends_at.astimezone(project_timezone).date()
        if end_date <= capacity.final_lock_date:
            preopening += seconds
        elif (
            start_date > capacity.final_lock_date
            and end_date <= capacity.novel_completion_date
        ):
            evaluation += seconds
    if (
        preopening < capacity.compute_slack * capacity.remaining_preopening_seconds
        or evaluation < capacity.compute_slack * capacity.remaining_evaluation_seconds
    ):
        raise ValueError("dated allocation windows do not fit remaining work and slack")
    recorded_date = as_of.astimezone(project_timezone).date()
    week_start = recorded_date - timedelta(days=recorded_date.weekday())
    before_hours = sum(
        hours
        for day, hours in availability.guaranteed_weekly_hours.items()
        if week_start <= day <= capacity.novel_completion_date
    )
    delivery_hours = sum(
        hours
        for day, hours in availability.guaranteed_weekly_hours.items()
        if date(2026, 12, 7) <= day <= date(2026, 12, 18)
    )
    delivery_work = capacity.researcher_work_hours["final_analysis_delivery"]
    before_work = sum(capacity.researcher_work_hours.values()) - delivery_work
    if (
        before_hours < capacity.researcher_slack * before_work
        or delivery_hours < capacity.researcher_slack * delivery_work
    ):
        raise ValueError("confirmed planned hours do not fit remaining work and slack")


def _validate_authorization(protocol, authorization):
    from pose_embed.artifacts import sample_order_digest, validate_feature_artifact
    from pose_embed.data.manifest import load_manifest
    from pose_embed.evaluation.analysis import metadata_dependence_table_v3
    from pose_embed.evaluation.result import EvaluationResult
    from pose_embed.geometry_v3 import validate_geometry_panel
    from pose_embed.report import _feature_path_for_hash, _validate_retrieval_metrics
    from pose_embed.training.runner import validate_engineering_pilot

    root = resolve_scientific_paths(protocol).root
    design = require_v3_design(protocol)
    if (
        authorization.protocol_sha256 != protocol_digest(protocol)
        or authorization.design_lock_sha256
        != sha256_file(root / protocol.test_access.design_lock_relative_path)
        or authorization.recorded_at < design.recorded_at
    ):
        raise ValueError("selection authorization differs from the admitted design")
    pilots = {}
    pairing = set()
    for method, binding in authorization.pilot_records.items():
        path = _campaign_binding(root, protocol, binding)
        metrics = validate_engineering_pilot(path.parent)
        manifest = json.loads((path.parent / "run-manifest.json").read_text())
        if (
            path.name != "metrics.json"
            or metrics["objective"] != method
            or manifest["protocol_sha256"] != authorization.protocol_sha256
            or manifest.get("scientific_use_allowed") is not True
            or datetime.fromisoformat(manifest["ended_at"]) > authorization.recorded_at
        ):
            raise ValueError(
                "selection pilot has wrong identity/eligibility/chronology"
            )
        pilots[method] = metrics["checkpoint_sha256"]
        pairing.add((metrics["initialization_sha256"], metrics["batch_plan_sha256"]))
    if len(pairing) != 1:
        raise ValueError("selection pilots are not paired")
    corruption = _receipt(
        root,
        authorization.corruption_verification,
        CorruptionReceipt,
        protocol,
        authorization,
    )
    if set(corruption.checks) != GEOMETRY_CHECKS or set(corruption.encodings) != set(
        CONDITIONS
    ):
        raise ValueError(
            "corruption admission requires all geometry checks and nine encodings"
        )
    query_manifest = _bound_file(root, design.manifests["development_queries"])
    expected_ids = tuple(row.sample_id for row in load_manifest(query_manifest))
    if corruption.query_sample_order_sha256 != sample_order_digest(expected_ids):
        raise ValueError("corruption admission changed the fixed development episode")
    validate_geometry_panel(
        _campaign_binding(root, protocol, corruption.geometry_panel), protocol
    )
    for condition, binding in corruption.encodings.items():
        sidecar = validate_feature_artifact(
            _campaign_binding(root, protocol, binding),
            protocol=protocol,
            manifest_path=query_manifest,
        )
        if (
            sidecar.condition != condition
            or sidecar.role != "query_corrupted"
            or not sidecar.scientific_use_allowed
            or sidecar.sample_ids != expected_ids
        ):
            raise ValueError("corruption cache identity/condition is invalid")
    cells = set()
    for binding in corruption.results:
        _campaign_binding(root, protocol, binding)
        result = _read(root, binding, EvaluationResult)
        cell = (result.method, result.condition)
        if (
            cell in cells
            or result.method not in pilots
            or result.seed != 7
            or result.condition not in CONDITIONS
            or result.mode != "engineering"
            or result.query_definition != "development"
            or result.protocol_sha256 != authorization.protocol_sha256
            or result.checkpoint_sha256 != pilots[result.method]
            or tuple(row.sample_id for row in result.metrics.per_query) != expected_ids
            or result.metrics.gallery_count != 20
        ):
            raise ValueError(
                "corruption receipt requires all 27 paired pilot evaluations"
            )
        for path, digest in result.provenance.inputs.items():
            if sha256_file(path) != digest:
                raise ValueError("corruption evaluation input changed")
        paths_by_hash = {}
        for path, digest in result.provenance.inputs.items():
            paths_by_hash.setdefault(digest, []).append(Path(path))
        gallery_path = _feature_path_for_hash(
            paths_by_hash, result.gallery_artifact_sha256, label="gallery"
        )
        query_path = _feature_path_for_hash(
            paths_by_hash, result.query_artifact_sha256, label="query"
        )
        for path, manifest, role in (
            (
                gallery_path,
                _bound_file(root, design.manifests["development_gallery"]),
                "gallery_clean",
            ),
            (query_path, query_manifest, "query_corrupted"),
        ):
            sidecar = validate_feature_artifact(
                path, protocol=protocol, manifest_path=manifest
            )
            if (
                not sidecar.scientific_use_allowed
                or sidecar.role != role
                or sidecar.head_checkpoint_sha256 != pilots[result.method]
                or (
                    role == "query_corrupted"
                    and sidecar.base_artifact_sha256
                    != corruption.encodings[result.condition].sha256
                )
            ):
                raise ValueError(
                    "corruption projection does not reuse its bound pilot/cache"
                )
        _validate_retrieval_metrics(result, gallery_path, query_path)
        cells.add(cell)
    analysis = _receipt(
        root,
        authorization.analysis_verification,
        AnalysisReceipt,
        protocol,
        authorization,
    )
    if set(analysis.checks) != ANALYSIS_CHECKS:
        raise ValueError("analysis admission omits required command/report checks")
    for table, manifest in (
        (analysis.development_dependence_table, "development_queries"),
        (analysis.novel_metadata_dependence_table, "novel_query_primary"),
    ):
        identifiers = tuple(
            row.sample_id
            for row in load_manifest(_bound_file(root, design.manifests[manifest]))
        )
        if json.loads(
            _bound_file(root, table).read_text()
        ) != metadata_dependence_table_v3(identifiers):
            raise ValueError("dependence table differs from its locked query manifest")
    capacity = _receipt(
        root, authorization.capacity_report, CapacityReceipt, protocol, authorization
    )
    _validate_capacity_availability(root, capacity, as_of=authorization.recorded_at)
    seal = _receipt(
        root, authorization.seal_audit, SealReceipt, protocol, authorization
    )
    if seal.artifact_root_registry_sha256 != design.artifact_root_registry_sha256:
        raise ValueError("selection seal audit differs from the shared registry")
    matrix = _read(root, authorization.run_matrix, SelectionMatrix)
    _campaign_binding(root, protocol, authorization.run_matrix)
    if matrix.protocol_sha256 != authorization.protocol_sha256:
        raise ValueError("selection matrix differs from the protocol")
    from pose_embed.config import validate_experiment_against_protocol

    for slot in matrix.slots:
        config = load_experiment(_campaign_binding(root, protocol, slot.config))
        validate_experiment_against_protocol(config, protocol)
        if (config.objective, config.learning_rate, config.seed) != _slot_key(slot):
            raise ValueError("selection matrix configuration differs from its slot")
    return matrix


def require_selection_authorization(
    protocol: ProtocolV3Config,
) -> V3SelectionAuthorization:
    root = resolve_scientific_paths(protocol).root
    path = root / protocol.test_access.selection_authorization_relative_path
    if not path.is_file():
        raise ValueError("v3 selection requires measured campaign authorization")
    authorization = V3SelectionAuthorization.model_validate_json(path.read_text())
    _validate_authorization(protocol, authorization)
    return authorization


def record_selection_authorization(
    protocol: ProtocolV3Config, authorization: V3SelectionAuthorization
):
    from pose_embed.dataset_seal import dataset_access

    with dataset_access():
        _validate_authorization(protocol, authorization)
        path = (
            resolve_scientific_paths(protocol).root
            / protocol.test_access.selection_authorization_relative_path
        )
        write_immutable_json(path, authorization.model_dump(mode="json"))
    return authorization


def selected_configs_path(protocol: ProtocolV3Config) -> Path:
    return (
        resolve_scientific_paths(protocol).root
        / protocol.test_access.selection_authorization_relative_path
    ).with_name("selected-configs.v3.json")


def _selection_table(protocol, authorization, ledger, *, not_after=None):
    from pose_embed.training.runner import validate_v3_training_run

    root = resolve_scientific_paths(protocol).root
    matrix = _read(root, authorization.run_matrix, SelectionMatrix)
    slots = {_slot_key(slot): slot for slot in matrix.slots}
    if (
        ledger.protocol_sha256 != protocol_digest(protocol)
        or ledger.run_matrix_sha256 != authorization.run_matrix.sha256
        or {_slot_key(slot) for slot in ledger.slots} != set(slots)
    ):
        raise ValueError("selection ledger must account for the same exact 27 slots")
    scores = {}
    attempt_ids = set()
    attempt_paths = set()
    pairing = {}
    for slot in ledger.slots:
        previous = None
        previous_id = None
        previous_identity = None
        previous_ended = None
        for index, record in enumerate(slot.attempts):
            path = _campaign_binding(root, protocol, record.attempt)
            attempt = json.loads(path.read_text())
            attempt_id = attempt["attempt_id"]
            started_at = datetime.fromisoformat(attempt["started_at"])
            _timestamp(started_at)
            identity = tuple(
                attempt.get(name)
                for name in (
                    "objective",
                    "seed",
                    "config_sha256",
                    "input_artifact_sha256",
                    "feature_sidecar_sha256",
                    "manifest_sha256",
                )
            )
            if (
                path.name != "attempt.json"
                or attempt_id in attempt_ids
                or attempt["protocol_sha256"] != ledger.protocol_sha256
                or attempt.get("stage") != "development_selection"
                or attempt.get("scientific_use_allowed") is not True
                or (attempt.get("objective"), attempt.get("seed"))
                != (slot.method, slot.seed)
                or attempt["config_sha256"] != slots[_slot_key(slot)].config.sha256
                or started_at < authorization.recorded_at
                or record.retry_of != previous_id
                or (previous_identity is not None and identity != previous_identity)
            ):
                raise ValueError(
                    "selection attempt identity, timing or retry lineage differs"
                )
            attempt_ids.add(attempt_id)
            attempt_paths.add(path.resolve())
            for evidence in record.evidence:
                _bound_file(root, evidence)
            if index and (
                previous.failure != "infrastructure" or not previous.evidence
            ):
                raise ValueError(
                    "only evidenced infrastructure failures permit identical retries"
                )
            if index and (previous_ended is None or started_at < previous_ended):
                raise ValueError("retry requires terminal accounting before its start")
            if index > 1:
                if record.remedy is None:
                    raise ValueError(
                        "additional retry requires diagnosis/remedy "
                        "and renewed capacity"
                    )
                remedy = json.loads(_bound_file(root, record.remedy).read_text())
                if not remedy.get("diagnosis") or not remedy.get("remedy"):
                    raise ValueError("additional retry lacks diagnosis/remedy")
                renewed = _receipt(
                    root,
                    ArtifactBinding.model_validate(remedy["capacity_report"]),
                    CapacityReceipt,
                    protocol,
                    authorization.model_copy(update={"recorded_at": started_at}),
                )
                if renewed.recorded_at < previous_ended:
                    raise ValueError("renewed capacity must follow the prior failure")
                _validate_capacity_availability(root, renewed, as_of=started_at)
            outcome = (
                json.loads(_bound_file(root, record.outcome).read_text())
                if record.outcome
                else None
            )
            if record.outcome is not None and (
                Path(record.outcome.relative_path).name != "outcome.json"
                or Path(record.outcome.relative_path).parent
                != Path(record.attempt.relative_path).parent
            ):
                raise ValueError("selection attempt requires its own outcome path")
            if outcome is not None and outcome["attempt_id"] != attempt_id:
                raise ValueError("selection outcome belongs to another attempt")
            if outcome is not None:
                ended_at = datetime.fromisoformat(outcome["ended_at"])
                _timestamp(ended_at)
                if ended_at < started_at or (
                    not_after is not None and ended_at > not_after
                ):
                    raise ValueError("selection outcome has invalid chronology")
                previous_ended = ended_at
            else:
                previous_ended = None
            if record.failure is None:
                if (
                    outcome is None
                    or outcome.get("status") != "success"
                    or index != len(slot.attempts) - 1
                ):
                    raise ValueError(
                        "successful attempt requires its own completed outcome"
                    )
                metrics = validate_v3_training_run(
                    path.parent, stage="development_selection"
                )
                epoch = json.loads((path.parent / "epoch-020.json").read_text())
                hashes = (
                    metrics["initialization_sha256"],
                    metrics["batch_plan_sha256"],
                )
                if slot.seed in pairing and pairing[slot.seed] != hashes:
                    raise ValueError(
                        "selection initialization and physical batches are not paired"
                    )
                pairing[slot.seed] = hashes
                scores[_slot_key(slot)] = (
                    epoch["scores"]["top1"],
                    epoch["scores"]["mrr"],
                )
            elif not record.evidence or (
                outcome is not None and outcome.get("status") != "failed"
            ):
                raise ValueError("failed attempts require preserved failure evidence")
            if record.failure == "implementation":
                raise ValueError(
                    "implementation/provenance defect blocks the selection stage; "
                    "record a result-blind correction and revalidate every "
                    "affected comparison"
                )
            previous, previous_id, previous_identity = record, attempt_id, identity
    for path in root.rglob("attempt.json"):
        attempt = json.loads(path.read_text())
        if (
            attempt.get("protocol_sha256") == ledger.protocol_sha256
            and attempt.get("stage") == "development_selection"
            and path.resolve() not in attempt_paths
        ):
            raise ValueError("selection ledger omits a preserved selection attempt")
    candidates = []
    selected = {}
    for method in protocol.objectives.core:
        valid = []
        for trial in protocol.training.tuning_grid:
            values = [
                scores.get((method, trial.learning_rate, seed))
                for seed in protocol.training.seeds
            ]
            eligible = all(value is not None for value in values)
            row = {
                "method": method,
                "learning_rate": trial.learning_rate,
                "eligible": eligible,
                "mean_top1": sum(value[0] for value in values) / 3
                if eligible
                else None,
                "mean_mrr": sum(value[1] for value in values) / 3 if eligible else None,
                "valid_seeds": [
                    seed
                    for seed, value in zip(protocol.training.seeds, values, strict=True)
                    if value is not None
                ],
                "ineligible_reason": None if eligible else "requires_three_valid_seeds",
            }
            candidates.append(row)
            if eligible:
                valid.append(row)
        if not valid:
            raise ValueError(f"no eligible three-seed candidate for {method}")
        selected[method] = max(
            valid,
            key=lambda row: (row["mean_top1"], row["mean_mrr"], -row["learning_rate"]),
        )["learning_rate"]
    return tuple(candidates), selected


def create_selected_configs(protocol, ledger: ArtifactBinding, *, recorded_by: str):
    from datetime import UTC

    from pose_embed.dataset_seal import dataset_access

    with dataset_access():
        authorization = require_selection_authorization(protocol)
        root = resolve_scientific_paths(protocol).root
        _campaign_binding(root, protocol, ledger)
        candidates, rates = _selection_table(
            protocol, authorization, _read(root, ledger, SelectionLedger)
        )
        selected = SelectedConfigurations(
            schema_version=1,
            kind="v3_selected_configurations",
            protocol_sha256=protocol_digest(protocol),
            selection_authorization_sha256=sha256_file(
                root / protocol.test_access.selection_authorization_relative_path
            ),
            recorded_at=datetime.now(UTC),
            recorded_by=recorded_by,
            ledger=ledger,
            candidates=candidates,
            selected_rates=rates,
        )
        write_immutable_json(
            selected_configs_path(protocol), selected.model_dump(mode="json")
        )
    return selected


def require_selected_configurations(protocol) -> SelectedConfigurations:
    authorization = require_selection_authorization(protocol)
    root = resolve_scientific_paths(protocol).root
    selected = SelectedConfigurations.model_validate_json(
        selected_configs_path(protocol).read_text()
    )
    _timestamp(selected.recorded_at)
    _campaign_binding(root, protocol, selected.ledger)
    if (
        selected.protocol_sha256 != protocol_digest(protocol)
        or selected.selection_authorization_sha256
        != sha256_file(
            root / protocol.test_access.selection_authorization_relative_path
        )
        or selected.recorded_at < authorization.recorded_at
    ):
        raise ValueError(
            "selected configurations have different authorization or chronology"
        )
    candidates, rates = _selection_table(
        protocol,
        authorization,
        _read(root, selected.ledger, SelectionLedger),
        not_after=selected.recorded_at,
    )
    if selected.candidates != candidates or selected.selected_rates != rates:
        raise ValueError(
            "selected configurations do not reproduce from all clean attempts"
        )
    return selected


def require_selected_configuration(
    protocol, config: ExperimentConfig
) -> SelectedConfigurations:
    from pose_embed.config import validate_experiment_against_protocol

    validate_experiment_against_protocol(config, protocol)
    selected = require_selected_configurations(protocol)
    if selected.selected_rates.get(config.objective) != config.learning_rate:
        raise ValueError(
            "final training configuration differs from clean selected rate"
        )
    return selected
