"""Typed, fail-closed configuration loading."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Base model that rejects misspelled or unplanned configuration fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ScheduleConfig(StrictModel):
    starts_on: date
    ends_on: date
    core_results_due_on: date

    @model_validator(mode="after")
    def dates_are_ordered(self) -> ScheduleConfig:
        if not self.starts_on <= self.core_results_due_on <= self.ends_on:
            raise ValueError("schedule dates must be ordered")
        return self


class DatasetConfig(StrictModel):
    name: str
    representation: str
    frames: int = Field(gt=0)
    joints: int = Field(gt=0)
    expected_source_sample_count: Literal[114480]
    novel_actions: tuple[int, ...]
    development_validation_actions: tuple[int, ...]
    official_protocol_source_url: str
    official_protocol_source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    official_one_shot_exemplars: tuple[str, ...]
    exclude_anchor_performance_views_from_primary_queries: bool

    @model_validator(mode="after")
    def action_partitions_are_valid(self) -> DatasetConfig:
        novel = set(self.novel_actions)
        validation = set(self.development_validation_actions)
        if len(novel) != 20 or len(validation) != 20:
            raise ValueError("novel and development-validation sets need 20 actions")
        if novel & validation:
            raise ValueError(
                "novel and development-validation actions must be disjoint"
            )
        if any(action < 1 or action > 120 for action in novel | validation):
            raise ValueError("NTU RGB+D 120 action IDs must lie in [1, 120]")
        expected_exemplars = (
            "S001C003P008R001A001",
            "S001C003P008R001A007",
            "S001C003P008R001A013",
            "S001C003P008R001A019",
            "S001C003P008R001A025",
            "S001C003P008R001A031",
            "S001C003P008R001A037",
            "S001C003P008R001A043",
            "S001C003P008R001A049",
            "S001C003P008R001A055",
            "S018C003P008R001A061",
            "S018C003P008R001A067",
            "S018C003P008R001A073",
            "S018C003P008R001A079",
            "S018C003P008R001A085",
            "S018C003P008R001A091",
            "S018C003P008R001A097",
            "S018C003P008R001A103",
            "S018C003P008R001A109",
            "S018C003P008R001A115",
        )
        if self.official_one_shot_exemplars != expected_exemplars:
            raise ValueError(
                "official NTU one-shot exemplars differ from the pinned protocol"
            )
        if {
            int(sample_id[-3:]) for sample_id in self.official_one_shot_exemplars
        } != novel:
            raise ValueError(
                "official one-shot exemplars must cover each novel action once"
            )
        expected_source_url = (
            "https://github.com/shahroudy/NTURGB-D/blob/"
            f"{self.official_protocol_source_commit}/README.md"
        )
        if self.official_protocol_source_url != expected_source_url:
            raise ValueError(
                "official protocol source must pin the declared Git commit"
            )
        return self


class InputPipelineConfig(StrictModel):
    tensor_layout: Literal["people_frames_joints_channels"]
    dtype: Literal["float32"]
    raw_joint_convention: Literal["coco17_hrnet"]
    encoder_joint_convention: Literal["h36m17_motionbert"]
    channels: tuple[Literal["x", "y", "confidence"], ...]
    encoder_joint_names: tuple[str, ...]
    coco_to_h36m_sources: tuple[tuple[int, ...], ...]
    derived_coordinate_rule: Literal["arithmetic_mean_of_sources"]
    derived_confidence_rule: Literal["minimum_of_source_confidences"]
    confidence_compatibility: Literal[
        "local_corrected_h36m_mapping_not_upstream_bit_parity"
    ]
    parity_layers: tuple[
        Literal[
            "camera_normalization",
            "person_tracking",
            "coordinate_mapping",
            "temporal_sampling",
            "single_person_padding",
            "spatial_normalization",
            "encoder_representation",
            "action_head",
        ],
        ...,
    ]
    camera_normalization: Literal[
        "divide_xy_by_long_image_side_multiply_two_subtract_one"
    ]
    person_tracking: Literal["motionbert_two_person_minimum_frame_displacement"]
    temporal_sampling: Literal["deterministic_uniform_floor_100_frames"]
    single_person_padding: Literal["append_one_all_zero_person"]
    spatial_normalization: Literal[
        "valid_confidence_bbox_crop_scale_ratio_one_clip_minus_one_plus_one"
    ]
    random_move: Literal[False]
    operation_order: tuple[str, ...]
    corruption_stage: Literal["after_preprocessing_before_frozen_encoder"]

    @model_validator(mode="after")
    def mapping_is_fully_specified(self) -> InputPipelineConfig:
        expected_names = (
            "pelvis",
            "right_hip",
            "right_knee",
            "right_ankle",
            "left_hip",
            "left_knee",
            "left_ankle",
            "belly",
            "neck",
            "nose",
            "head",
            "left_shoulder",
            "left_elbow",
            "left_wrist",
            "right_shoulder",
            "right_elbow",
            "right_wrist",
        )
        expected_sources = (
            (11, 12),
            (12,),
            (14,),
            (16,),
            (11,),
            (13,),
            (15,),
            (11, 12, 5, 6),
            (5, 6),
            (0,),
            (1, 2),
            (5,),
            (7,),
            (9,),
            (6,),
            (8,),
            (10,),
        )
        expected_order = (
            "camera_normalization",
            "person_tracking",
            "joint_and_confidence_conversion",
            "temporal_sampling",
            "single_person_padding",
            "spatial_normalization",
        )
        if self.channels != ("x", "y", "confidence"):
            raise ValueError("encoder channels must be exactly x, y, confidence")
        if self.encoder_joint_names != expected_names:
            raise ValueError("encoder joint order must be the locked H36M17 convention")
        if self.coco_to_h36m_sources != expected_sources:
            raise ValueError("COCO-to-H36M mapping differs from protocol v1")
        if self.operation_order != expected_order:
            raise ValueError("preprocessing operation order differs from protocol v1")
        expected_parity_layers = (
            "camera_normalization",
            "person_tracking",
            "coordinate_mapping",
            "temporal_sampling",
            "single_person_padding",
            "spatial_normalization",
            "encoder_representation",
            "action_head",
        )
        if self.parity_layers != expected_parity_layers:
            raise ValueError("MotionBERT parity layers differ from protocol v1")
        return self


class EncoderConfig(StrictModel):
    name: str
    frozen: bool
    evaluation_mode: bool
    representation_dimension: int = Field(gt=0)
    embedding_dimension: int = Field(gt=0)
    people: int = Field(gt=0)

    @model_validator(mode="after")
    def encoder_is_frozen(self) -> EncoderConfig:
        if not self.frozen or not self.evaluation_mode:
            raise ValueError("protocol v1 requires a frozen encoder in evaluation mode")
        return self


class BatchConfig(StrictModel):
    classes_per_batch: int = Field(gt=1)
    samples_per_class: int = Field(gt=1)
    physical_batch_size: int = Field(gt=0)
    profile_batch_size: int = Field(gt=0)

    @model_validator(mode="after")
    def physical_size_matches_pk(self) -> BatchConfig:
        if self.classes_per_batch * self.samples_per_class != self.physical_batch_size:
            raise ValueError(
                "physical_batch_size must equal classes_per_batch * samples_per_class"
            )
        if self.samples_per_class % 2:
            raise ValueError("samples_per_class must be even for contextual loss")
        return self


class ContextualProtocolConfig(StrictModel):
    epsilon: float = Field(ge=0)
    straight_through_alpha: float = Field(gt=0)
    contextual_weight: float = Field(ge=0, le=1)
    regularizer_weight: float = Field(ge=0)
    target_mean_similarity: float
    positive_margin: float
    negative_margin: float
    neighborhood_size: int = Field(gt=1)
    normalize_embeddings: Literal[True]
    comparison_operator: Literal["greater_than_or_equal_with_constant_ste_gradient"]

    @model_validator(mode="after")
    def margins_are_ordered(self) -> ContextualProtocolConfig:
        if self.positive_margin < self.negative_margin:
            raise ValueError("positive_margin must be >= negative_margin")
        return self


class StretchProtocolConfig(StrictModel):
    method: Literal["multi_similarity_with_miner"]
    exploratory_only: Literal[True]
    predeclared_hyperparameters_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    library: Literal["pytorch-metric-learning"]
    library_version: Literal["2.9.0"]
    loss_alpha: float
    loss_beta: float
    loss_base: float
    miner_epsilon: float
    distance: Literal["cosine_similarity"]
    normalize_embeddings: Literal[True]
    distance_p: Literal[2]
    distance_power: Literal[1]
    entry_gates: tuple[str, ...]

    @model_validator(mode="after")
    def all_core_gates_are_required(self) -> StretchProtocolConfig:
        expected = (
            "nine_core_checkpoints_verified",
            "full_core_result_matrix_verified",
            "core_figures_reproducible",
            "no_unresolved_core_failures",
        )
        if self.entry_gates != expected:
            raise ValueError("stretch entry gates differ from the locked four gates")
        if (
            self.loss_alpha,
            self.loss_beta,
            self.loss_base,
            self.miner_epsilon,
        ) != (2.0, 50.0, 0.5, 0.1):
            raise ValueError("Multi-Similarity parameters differ from protocol v1")
        return self


class ContrastiveProtocolConfig(StrictModel):
    positive_margin: float
    negative_margin: float
    normalize_embeddings: Literal[True]

    @model_validator(mode="after")
    def margins_are_v1(self) -> ContrastiveProtocolConfig:
        if (self.positive_margin, self.negative_margin) != (0.9, 0.6):
            raise ValueError("contrastive margins differ from protocol v1")
        return self


class SupConProtocolConfig(StrictModel):
    temperature: float
    normalize_embeddings: Literal[True]

    @model_validator(mode="after")
    def temperature_is_v1(self) -> SupConProtocolConfig:
        if self.temperature != 0.07:
            raise ValueError("SupCon temperature differs from protocol v1")
        return self


class ObjectivesConfig(StrictModel):
    core: tuple[Literal["contrastive", "supcon", "contextual"], ...]
    contrastive: ContrastiveProtocolConfig
    supcon: SupConProtocolConfig
    contextual: ContextualProtocolConfig
    stretch: StretchProtocolConfig

    @model_validator(mode="after")
    def core_is_complete(self) -> ObjectivesConfig:
        if set(self.core) != {"contrastive", "supcon", "contextual"}:
            raise ValueError(
                "core objectives must be contrastive, supcon, and contextual"
            )
        if (
            self.contextual.positive_margin != self.contrastive.positive_margin
            or self.contextual.negative_margin != self.contrastive.negative_margin
        ):
            raise ValueError(
                "contextual and contrastive components must share exact margins"
            )
        return self


class TrainingProtocolConfig(StrictModel):
    seeds: tuple[int, ...]
    tuning_trials_per_method: int = Field(gt=0)
    tune_on: Literal["development_validation_clean_only"]
    epochs: int = Field(gt=0)
    optimizer: Literal["adamw"]
    tuning_grid: tuple[TuningTrial, ...]
    initial_screen_seed: int
    retain_candidates_per_method: int = Field(gt=0)
    final_selection_metric: Literal["top1"]
    final_selection_aggregation: Literal["mean_across_three_paired_seeds"]
    final_selection_tie_breakers: tuple[
        Literal["higher_mrr", "lower_seed_standard_deviation", "lexical_config_id"],
        ...,
    ]
    paired_initialization: Literal["same_seed_same_linear_state_across_methods"]
    paired_batch_plan: Literal[
        "same_seed_epoch_and_ordered_sample_indices_across_methods"
    ]
    gradient_accumulation_equivalent: Literal[False]
    failed_run_policy: FailedRunPolicy

    @model_validator(mode="after")
    def has_three_distinct_seeds(self) -> TrainingProtocolConfig:
        if len(self.seeds) != 3 or len(set(self.seeds)) != 3:
            raise ValueError("protocol v1 requires three distinct paired seeds")
        if len(self.tuning_grid) != self.tuning_trials_per_method:
            raise ValueError("tuning grid must contain the declared trial count")
        if len(set(self.tuning_grid)) != len(self.tuning_grid):
            raise ValueError("tuning grid entries must be unique")
        if self.initial_screen_seed not in self.seeds:
            raise ValueError("initial screen seed must be one of the paired seeds")
        expected_grid = (
            TuningTrial(learning_rate=0.001, weight_decay=0.0),
            TuningTrial(learning_rate=0.001, weight_decay=0.0001),
            TuningTrial(learning_rate=0.0003, weight_decay=0.0),
            TuningTrial(learning_rate=0.0003, weight_decay=0.0001),
            TuningTrial(learning_rate=0.0001, weight_decay=0.0),
            TuningTrial(learning_rate=0.0001, weight_decay=0.0001),
        )
        if self.tuning_grid != expected_grid:
            raise ValueError("tuning grid differs from the six equal-budget trials")
        return self


class TuningTrial(StrictModel):
    learning_rate: float = Field(gt=0)
    weight_decay: float = Field(ge=0)


class FailedRunPolicy(StrictModel):
    preserve_every_attempt: Literal[True]
    infrastructure_failure: Literal[
        "rerun_same_config_seed_initialization_and_batch_plan_from_scratch"
    ]
    numerical_failure: Literal[
        "mark_failed_debug_on_development_only_and_require_amendment_for_parameter_change"
    ]
    seed_replacement: Literal["forbidden"]
    novel_outcome_based_rerun: Literal["forbidden"]


class TorsoJointIndices(StrictModel):
    left_shoulder: Literal[11]
    right_shoulder: Literal[14]
    left_hip: Literal[4]
    right_hip: Literal[1]


class AmendmentPolicy(StrictModel):
    allowed_until: Literal["before_tuning_ends_and_before_test_opening"]
    allowed_reason: Literal["geometric_invalid_imperceptible_or_degenerate_only"]
    retrieval_score_motivated_change: Literal["forbidden"]
    advisor_approval_required: Literal[True]
    new_protocol_hash_and_lock_required: Literal[True]


class CorruptionConfig(StrictModel):
    query_only: bool
    joint_convention: Literal["h36m17_motionbert"]
    required_channels: tuple[Literal["x", "y", "confidence"], ...]
    coordinate_jitter_fractions: tuple[float, ...]
    jitter_distribution: Literal["independent_zero_mean_gaussian_xy"]
    jitter_scale: Literal["median_distance_between_shoulder_midpoint_and_hip_midpoint"]
    torso_joint_indices: TorsoJointIndices
    jitter_support: Literal["confidence_greater_than_zero_only"]
    jitter_confidence_behavior: Literal["unchanged"]
    joint_mask_counts: tuple[int, ...]
    joint_mask_groups: tuple[tuple[int, ...], ...]
    joint_selection: Literal["seeded_group_order_then_proximal_to_distal_unique_prefix"]
    consecutive_frame_mask_counts: tuple[int, ...]
    frame_selection: Literal[
        "one_seeded_contiguous_block_shared_across_people_and_joints"
    ]
    masking_value: float
    masking_channels: tuple[Literal["x", "y", "confidence"], ...]
    preserve_tensor_shape: Literal[True]
    severity_zero: Literal["byte_identical_copy"]
    seed_derivation: Literal[
        "sha256_protocol_id_sample_id_family_canonical_severity_first_63_bits"
    ]
    gallery_corruption: Literal["forbidden"]
    amendments: AmendmentPolicy

    @model_validator(mode="after")
    def corruption_grid_is_valid(self) -> CorruptionConfig:
        if not self.query_only:
            raise ValueError("protocol v1 corrupts queries only")
        if len(self.coordinate_jitter_fractions) != 3:
            raise ValueError("coordinate jitter requires exactly three levels")
        if len(self.joint_mask_counts) != 3:
            raise ValueError("joint masking requires exactly three levels")
        if len(self.consecutive_frame_mask_counts) != 3:
            raise ValueError("frame masking requires exactly three levels")
        if any(value <= 0 for value in self.coordinate_jitter_fractions):
            raise ValueError("jitter levels must be positive")
        if any(value <= 0 for value in self.joint_mask_counts):
            raise ValueError("joint mask counts must be positive")
        if any(value <= 0 for value in self.consecutive_frame_mask_counts):
            raise ValueError("frame mask counts must be positive")
        if self.coordinate_jitter_fractions != (0.01, 0.025, 0.05):
            raise ValueError("coordinate jitter levels differ from protocol v1")
        if self.joint_mask_counts != (3, 6, 8):
            raise ValueError("joint-mask levels differ from protocol v1")
        if self.consecutive_frame_mask_counts != (10, 25, 40):
            raise ValueError("frame-mask levels differ from protocol v1")
        if self.required_channels != ("x", "y", "confidence"):
            raise ValueError("corruptions require x, y, confidence channels")
        if self.masking_channels != self.required_channels:
            raise ValueError("masking must zero x, y, and confidence")
        flattened = [joint for group in self.joint_mask_groups for joint in group]
        if sorted(flattened) != list(range(17)):
            raise ValueError("joint mask groups must partition H36M17 exactly once")
        return self


class AnalysisConfig(StrictModel):
    metrics: tuple[Literal["top1", "mrr", "r_at_5"], ...]
    bootstrap_replicates: int = Field(gt=0)
    bootstrap_cluster: tuple[str, ...]
    confidence_level: float = Field(gt=0, lt=1)
    primary_comparison: Literal["contextual_minus_contrastive_degradation"]
    observation: Literal["paired_query_top1_correctness"]
    cell_weighting: Literal["equal_across_three_seeds_and_nine_corruption_cells"]
    effect_direction: Literal["negative_means_contextual_degraded_less"]
    support_rule: Literal["upper_confidence_bound_below_zero"]
    claim_caveat: Literal[
        "less_degradation_is_not_higher_overall_retrieval_when_clean_accuracy_differs"
    ]
    required_reporting: tuple[str, ...]
    confirmatory_methods: tuple[Literal["contrastive", "contextual"], ...]
    secondary_methods: tuple[Literal["supcon", "multi_similarity_with_miner"], ...]

    @model_validator(mode="after")
    def analysis_is_complete(self) -> AnalysisConfig:
        if self.metrics != ("top1", "mrr", "r_at_5"):
            raise ValueError("analysis requires exactly top-1, MRR, and R@5")
        if self.bootstrap_cluster != ("setup", "performer", "repetition", "action"):
            raise ValueError("bootstrap cluster identity differs from protocol v1")
        if self.confirmatory_methods != ("contrastive", "contextual"):
            raise ValueError("confirmatory methods differ from protocol v1")
        if self.secondary_methods != ("supcon", "multi_similarity_with_miner"):
            raise ValueError("secondary methods differ from protocol v1")
        expected_reporting = (
            "clean_accuracy",
            "every_seed",
            "every_corruption_curve",
            "runtime",
            "memory",
            "failures",
        )
        if self.required_reporting != expected_reporting:
            raise ValueError("required reporting set differs from protocol v1")
        return self


class TestAccessConfig(StrictModel):
    state: Literal["sealed"]
    final_evaluation_requires_lock: Literal[True]
    evaluation_plan_template: Literal["configs/evaluation-plan.v1.yaml"]
    artifact_root_environment: Literal["POSE_EMBED_ARTIFACT_ROOT"]
    protocol_lock_relative_path: Literal["locks/protocol-lock.v1.json"]
    evaluation_plan_relative_path: Literal["locks/evaluation-plan.v1.yaml"]
    final_run_set_relative_path: Literal["locks/final-run-set.v1.json"]
    opening_ledger_relative_path: Literal["locks/test-opening.v1.json"]
    stretch_gate_evidence_relative_path: Literal["locks/stretch-gates.v1.json"]
    opening_policy: Literal["one_atomic_immutable_ledger_event"]
    ledger_reuse: Literal["same_protocol_lock_evaluation_plan_and_run_set_hashes_only"]
    reject_future_lock_timestamps: Literal[True]
    training_after_opening: Literal[
        "core_forbidden_exploratory_stretch_requires_verified_gates"
    ]
    confirmatory_changes_after_opening: Literal["forbidden"]


class ProtocolConfig(StrictModel):
    schema_version: Literal[1]
    protocol_id: Literal["protocol-v1"]
    title: str
    timezone: Literal["America/New_York"]
    schedule: ScheduleConfig
    research_question: str
    dataset: DatasetConfig
    input_pipeline: InputPipelineConfig
    encoder: EncoderConfig
    batch: BatchConfig
    objectives: ObjectivesConfig
    training: TrainingProtocolConfig
    corruptions: CorruptionConfig
    analysis: AnalysisConfig
    test_access: TestAccessConfig

    @model_validator(mode="after")
    def components_are_cross_consistent(self) -> ProtocolConfig:
        if self.objectives.contextual.neighborhood_size != (
            self.batch.samples_per_class
        ):
            raise ValueError("contextual neighborhood must equal physical batch K")
        return self


class ContextualExperimentConfig(StrictModel):
    epsilon: float = Field(ge=0)
    straight_through_alpha: float = Field(gt=0)
    contextual_weight: float = Field(ge=0, le=1)
    regularizer_weight: float = Field(ge=0)
    target_mean_similarity: float


class MultiSimilarityExperimentConfig(StrictModel):
    library: Literal["pytorch-metric-learning"]
    library_version: Literal["2.9.0"]
    loss_alpha: float
    loss_beta: float
    loss_base: float
    miner_epsilon: float
    distance: Literal["cosine_similarity"]
    normalize_embeddings: Literal[True]
    distance_p: Literal[2]
    distance_power: Literal[1]

    @model_validator(mode="after")
    def parameters_are_pinned(self) -> MultiSimilarityExperimentConfig:
        if (
            self.loss_alpha,
            self.loss_beta,
            self.loss_base,
            self.miner_epsilon,
        ) != (2.0, 50.0, 0.5, 0.1):
            raise ValueError("Multi-Similarity parameters must use pinned v1 values")
        return self


class ExperimentConfig(StrictModel):
    schema_version: Literal[1]
    name: str
    objective: Literal[
        "contrastive",
        "supcon",
        "contextual",
        "multi_similarity_with_miner",
    ]
    seed: int
    input_dimension: int = Field(gt=0)
    embedding_dimension: int = Field(gt=0)
    epochs: int = Field(gt=0)
    learning_rate: float = Field(gt=0)
    weight_decay: float = Field(ge=0)
    classes_per_batch: int = Field(gt=1)
    samples_per_class: int = Field(gt=1)
    temperature: float = Field(gt=0)
    positive_margin: float
    negative_margin: float
    contextual: ContextualExperimentConfig | None = None
    multi_similarity: MultiSimilarityExperimentConfig | None = None

    @model_validator(mode="after")
    def objective_parameters_are_valid(self) -> ExperimentConfig:
        if self.positive_margin < self.negative_margin:
            raise ValueError("positive_margin must be >= negative_margin")
        if self.objective == "contextual" and self.contextual is None:
            raise ValueError("contextual objective requires contextual settings")
        if self.objective != "contextual" and self.contextual is not None:
            raise ValueError("contextual settings are only valid for that objective")
        if self.objective == "multi_similarity_with_miner":
            if self.multi_similarity is None:
                raise ValueError(
                    "multi-similarity objective requires exact loss/miner settings"
                )
        elif self.multi_similarity is not None:
            raise ValueError(
                "multi-similarity settings are only valid for the stretch objective"
            )
        if self.samples_per_class % 2:
            raise ValueError("samples_per_class must be even")
        return self


def experiment_hyperparameters_digest(config: ExperimentConfig) -> str:
    """Hash method settings while excluding only per-run identity fields."""
    payload = config.model_dump(mode="json")
    payload.pop("name")
    payload.pop("seed")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"configuration file does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {path}: {exc}") from exc


def load_protocol(path: str | Path) -> ProtocolConfig:
    """Load and validate the machine-readable protocol."""
    return ProtocolConfig.model_validate(_load_yaml(Path(path)))


def load_experiment(path: str | Path) -> ExperimentConfig:
    """Load and validate one experiment configuration."""
    return ExperimentConfig.model_validate(_load_yaml(Path(path)))


def validate_experiment_against_protocol(
    experiment: ExperimentConfig,
    protocol: ProtocolConfig,
) -> None:
    """Reject experiment settings outside the preregistered search space."""
    allowed_objectives = {*protocol.objectives.core, protocol.objectives.stretch.method}
    if experiment.objective not in allowed_objectives:
        raise ValueError("experiment objective is absent from the protocol")
    if experiment.seed not in protocol.training.seeds:
        raise ValueError("experiment seed is absent from the paired seed set")
    expected_dimensions = (
        protocol.encoder.representation_dimension * protocol.dataset.joints,
        protocol.encoder.embedding_dimension,
    )
    if (experiment.input_dimension, experiment.embedding_dimension) != (
        expected_dimensions
    ):
        raise ValueError("experiment dimensions differ from the MotionBERT head")
    if experiment.epochs != protocol.training.epochs:
        raise ValueError("experiment epoch budget differs from the protocol")
    if (
        experiment.classes_per_batch,
        experiment.samples_per_class,
    ) != (protocol.batch.classes_per_batch, protocol.batch.samples_per_class):
        raise ValueError("experiment physical P x K batch differs from the protocol")
    trial = TuningTrial(
        learning_rate=experiment.learning_rate,
        weight_decay=experiment.weight_decay,
    )
    if trial not in protocol.training.tuning_grid:
        raise ValueError("experiment optimizer settings are outside the tuning grid")
    contrastive = protocol.objectives.contrastive
    if (
        experiment.positive_margin,
        experiment.negative_margin,
    ) != (contrastive.positive_margin, contrastive.negative_margin):
        raise ValueError("experiment contrastive margins differ from the protocol")
    if experiment.temperature != protocol.objectives.supcon.temperature:
        raise ValueError("experiment SupCon temperature differs from the protocol")
    if experiment.objective == "contextual":
        configured = experiment.contextual
        registered = protocol.objectives.contextual
        if configured is None or (
            configured.epsilon,
            configured.straight_through_alpha,
            configured.contextual_weight,
            configured.regularizer_weight,
            configured.target_mean_similarity,
        ) != (
            registered.epsilon,
            registered.straight_through_alpha,
            registered.contextual_weight,
            registered.regularizer_weight,
            registered.target_mean_similarity,
        ):
            raise ValueError("experiment contextual settings differ from the protocol")
    if experiment.objective == "multi_similarity_with_miner":
        configured_ms = experiment.multi_similarity
        registered_ms = protocol.objectives.stretch
        if (
            experiment_hyperparameters_digest(experiment)
            != registered_ms.predeclared_hyperparameters_sha256
        ):
            raise ValueError(
                "experiment differs from the predeclared Multi-Similarity config"
            )
        if configured_ms is None or configured_ms.model_dump() != {
            "library": registered_ms.library,
            "library_version": registered_ms.library_version,
            "loss_alpha": registered_ms.loss_alpha,
            "loss_beta": registered_ms.loss_beta,
            "loss_base": registered_ms.loss_base,
            "miner_epsilon": registered_ms.miner_epsilon,
            "distance": registered_ms.distance,
            "normalize_embeddings": registered_ms.normalize_embeddings,
            "distance_p": registered_ms.distance_p,
            "distance_power": registered_ms.distance_power,
        }:
            raise ValueError(
                "experiment Multi-Similarity settings differ from the protocol"
            )


def canonical_json(model: BaseModel) -> bytes:
    """Return deterministic JSON bytes used for protocol and run hashes."""
    payload = model.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
