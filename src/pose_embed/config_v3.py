"""Explicit v3 design; historical v1/v2 validators and recipes stay unchanged."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import Field, model_validator

from pose_embed.config import (
    BatchConfig,
    ContextualProtocolConfig,
    ContrastiveProtocolConfig,
    DatasetConfig,
    EncoderConfig,
    ExperimentConfig,
    FailedRunPolicy,
    InputPipelineConfig,
    ScheduleConfig,
    StrictModel,
    SupConProtocolConfig,
    TorsoJointIndices,
    TuningTrial,
)

SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ArtifactBinding(StrictModel):
    relative_path: str
    sha256: SHA256

    @model_validator(mode="after")
    def safe_relative_path(self) -> ArtifactBinding:
        path = PurePosixPath(self.relative_path)
        if (
            not self.relative_path
            or "\\" in self.relative_path
            or "\x00" in self.relative_path
            or path.is_absolute()
            or path.as_posix() != self.relative_path
            or any(part in {"", ".", ".."} for part in self.relative_path.split("/"))
        ):
            raise ValueError("artifact binding must be a normalized relative path")
        return self


class V3Preparation(StrictModel):
    auxiliary_container: ArtifactBinding
    fallback_evidence: ArtifactBinding
    fallback_value: float = Field(gt=0, allow_inf_nan=False)
    source_inventory: ArtifactBinding
    identities: ArtifactBinding
    encoder_checkpoint_sha256: SHA256
    upstream_sha256: dict[str, SHA256] = Field(min_length=1)

    @model_validator(mode="after")
    def all_encoder_assets_are_bound(self) -> V3Preparation:
        if set(self.upstream_sha256) != {
            "upstream_sha256",
            "config_sha256",
            "license_sha256",
        }:
            raise ValueError("v3 binds upstream, architecture and license hashes")
        return self


class V3Provenance(StrictModel):
    adopted_input_protocol_sha256: Literal[
        "c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f"
    ]
    historical_development_episode_sha256: Literal[
        "88f30f96e35dedfd34b42f8e8ee2b561db44bbaf1f93d82d0522ffe011abba46"
    ]
    development_anchor_prefix: Literal["protocol-v1|dev-anchor-v1|"]
    historical_aggregate_access: Literal[
        "all_annotations_deserialized_before_auxiliary_selection_no_novel_representation_or_outcome_access"
    ]
    historical_cache_policy: Literal["retain_unchanged_generate_fresh_v3_caches"]


class V3Objectives(StrictModel):
    core: tuple[Literal["contrastive", "supcon", "contextual"], ...]
    contrastive: ContrastiveProtocolConfig
    supcon: SupConProtocolConfig
    contextual: ContextualProtocolConfig
    optional_control: Literal["omitted_before_pilots_and_scores"]
    contextual_target: Literal["equation_5_same_label_indicator"]
    contextual_distance: Literal["clamp_2_minus_2_cosine_min_zero"]
    contextual_neighbors: Literal["include_self_detached_kth_threshold"]
    contextual_first_stage_counts: Literal["detached"]
    reciprocal_denominator: Literal["non_detached_clamp_min_one"]
    contextual_reduction: Literal["off_diagonal_squared_error_divided_by_n_squared"]
    contrastive_reduction: Literal["separate_strictly_active_hinge_means_empty_zero"]
    regularizer_reduction: Literal["mean_similarity_including_diagonal"]
    supcon_reduction: Literal[
        "single_view_positive_log_softmax_no_temperature_multiplier"
    ]

    @model_validator(mode="after")
    def exact_recipes(self) -> V3Objectives:
        if self.core != ("contrastive", "supcon", "contextual"):
            raise ValueError("v3 requires the exact three ordered arms")
        c = self.contextual
        if (
            c.epsilon,
            c.straight_through_alpha,
            c.contextual_weight,
            c.regularizer_weight,
            c.target_mean_similarity,
            c.positive_margin,
            c.negative_margin,
            c.neighborhood_size,
        ) != (0.05, 10.0, 0.4, 0.1, 0.25, 0.75, 0.6, 4):
            raise ValueError("contextual recipe differs from the v3 transfer recipe")
        return self


class V3Pilot(StrictModel):
    seed: Literal[7]
    learning_rate: Literal[0.0003]
    snapshot_epochs: tuple[Literal[5, 10, 15, 20], ...]
    diagnostic_epochs: tuple[Literal[0, 5, 10, 15, 20], ...]
    selection_eligible: Literal[False]
    fixture_updates: Literal[1000]
    fixture_self_excluded_top1: Literal[1.0]
    maximum_normalization_error: Literal[0.00001]
    minimum_query_variance_exclusive: Literal[0.000001]
    real_accuracy_floor: None

    @model_validator(mode="after")
    def exact_epochs(self) -> V3Pilot:
        if self.snapshot_epochs != (5, 10, 15, 20) or self.diagnostic_epochs != (
            0,
            5,
            10,
            15,
            20,
        ):
            raise ValueError("v3 pilot diagnostics and snapshots are fixed")
        return self


class V3Training(StrictModel):
    seeds: tuple[int, ...]
    tuning_trials_per_method: Literal[3]
    tune_on: Literal["development_validation_clean_only"]
    final_training_actions: Literal["all_100_auxiliary_actions"]
    insufficient_compute_policy: Literal[
        "block_and_require_documented_amendment_before_test_opening"
    ]
    epochs: Literal[20]
    optimizer: Literal["adamw"]
    tuning_grid: tuple[TuningTrial, ...]
    optimizer_betas: tuple[float, float]
    optimizer_epsilon: Literal[0.00000001]
    optimizer_amsgrad: Literal[False]
    weight_decay_scope: Literal["weight_and_bias"]
    scheduler: None
    mixed_precision: Literal[False]
    gradient_clipping: None
    augmentation: Literal[False]
    dtype: Literal["float32"]
    initialization: Literal["pytorch_linear_default"]
    head_bias: Literal[True]
    head_dropout: Literal[0.0]
    trainable_parameters: Literal[17827840]
    torch_version: Literal["2.9.1"]
    python_version: Literal["3.11"]
    numpy_version: Literal["2.4.6"]
    cublas_workspace_config: Literal[":4096:8"]
    deterministic_algorithms: Literal[True]
    allow_tf32: Literal[False]
    sampler: Literal["ceil_n_over_32_seed_plus_epoch_shuffled_queues_modular_cycle"]
    final_selection_metric: Literal["top1"]
    final_selection_aggregation: Literal["mean_across_three_paired_seeds"]
    final_selection_tie_breakers: tuple[
        Literal["higher_mrr", "lower_learning_rate"], ...
    ]
    selection_epoch: Literal[20]
    failed_candidate: Literal["ineligible_unless_all_three_seeds_valid"]
    selection_runs: Literal[27]
    final_runs: Literal[9]
    paired_initialization: Literal["same_seed_same_linear_state_across_methods"]
    paired_batch_plan: Literal[
        "same_seed_epoch_and_ordered_sample_indices_across_methods"
    ]
    gradient_accumulation_equivalent: Literal[False]
    failed_run_policy: FailedRunPolicy
    pilot: V3Pilot

    @model_validator(mode="after")
    def fixed_search_space(self) -> V3Training:
        if self.seeds != (7, 17, 29):
            raise ValueError("v3 seeds must be exactly 7, 17, 29")
        if tuple((t.learning_rate, t.weight_decay) for t in self.tuning_grid) != (
            (0.0001, 0.0001),
            (0.0003, 0.0001),
            (0.001, 0.0001),
        ):
            raise ValueError(
                "v3 has exactly three learning rates and fixed weight decay"
            )
        if self.optimizer_betas != (0.9, 0.999):
            raise ValueError("v3 AdamW betas are fixed")
        if self.final_selection_tie_breakers != ("higher_mrr", "lower_learning_rate"):
            raise ValueError("v3 tie breakers are mean MRR then lower learning rate")
        return self


class V3Corruptions(StrictModel):
    query_only: Literal[True]
    joint_convention: Literal["h36m17_motionbert"]
    required_channels: tuple[Literal["x", "y", "confidence"], ...]
    coordinate_jitter_fractions: tuple[float, ...]
    jitter_distribution: Literal["shared_cpu_float32_torch_gaussian_xy"]
    jitter_scale: Literal["lower_median_positive_finite_torso_distances"]
    torso_joint_indices: TorsoJointIndices
    jitter_support: Literal["confidence_greater_than_zero_only"]
    jitter_confidence_behavior: Literal["unchanged"]
    joint_mask_counts: tuple[int, ...]
    joint_mask_groups: tuple[tuple[int, ...], ...]
    joint_selection: Literal[
        "python_random_group_shuffle_then_fixed_within_group_prefix"
    ]
    consecutive_frame_mask_counts: tuple[int, ...]
    frame_selection: Literal["floor_u_times_101_minus_length_over_2_to_64"]
    masking_value: Literal[0.0]
    masking_channels: tuple[Literal["x", "y", "confidence"], ...]
    preserve_tensor_shape: Literal[True]
    severity_zero: Literal["byte_identical_copy"]
    seed_derivation: Literal[
        "sha256_protocol_id_nul_sample_id_nul_family_first_u64_and_low63"
    ]
    nested_severities: Literal[True]
    gallery_corruption: Literal["forbidden"]
    composition: Literal["forbidden_each_family_starts_clean"]
    post_corruption_processing: Literal["none"]
    fallback_rule: Literal[
        "lower_median_valid_sample_scales_80_action_development_train_only"
    ]
    amendments: Literal[
        "documented_result_blind_before_selection_new_protocol_and_affected_runs"
    ]

    @model_validator(mode="after")
    def exact_operators(self) -> V3Corruptions:
        if (
            self.coordinate_jitter_fractions != (0.01, 0.025, 0.05)
            or self.joint_mask_counts != (3, 6, 8)
            or self.consecutive_frame_mask_counts != (10, 25, 40)
            or self.joint_mask_groups
            != ((11, 12, 13), (14, 15, 16), (1, 2, 3), (4, 5, 6), (0, 7, 8, 9, 10))
            or self.required_channels != ("x", "y", "confidence")
            or self.masking_channels != self.required_channels
        ):
            raise ValueError("v3 corruption grid/groups/channels are fixed")
        return self


class V3Analysis(StrictModel):
    metrics: tuple[Literal["top1", "mrr", "r_at_5"], ...]
    bootstrap_replicates: Literal[10000]
    bootstrap_cluster: tuple[str, ...]
    bootstrap_stratification: Literal["within_each_fixed_action"]
    bootstrap_generator: Literal["numpy.random.Generator(PCG64(2026))"]
    bootstrap_query_weighting: Literal[
        "all_views_with_multiplicity_divide_by_sampled_query_count"
    ]
    bootstrap_pairing: Literal["one_draw_shared_across_methods_seeds_conditions"]
    resample_seeds: Literal[False]
    resample_actions: Literal[False]
    confidence_level: Literal[0.95]
    quantile_method: Literal["linear"]
    primary_comparison: Literal["contextual_minus_contrastive_degradation"]
    observation: Literal["paired_query_top1_correctness"]
    cell_weighting: Literal["equal_across_three_seeds_and_nine_corruption_cells"]
    effect_direction: Literal["negative_means_contextual_degraded_less"]
    support_rule: Literal["upper_confidence_bound_below_zero"]
    claim_caveat: Literal[
        "less_degradation_is_not_higher_overall_retrieval_when_clean_accuracy_differs"
    ]
    confirmatory_methods: tuple[Literal["contrastive", "contextual"], ...]
    secondary_methods: tuple[Literal["supcon"], ...]
    leave_one_action_out: Literal[
        "remove_queries_only_retain_all_gallery_anchors_and_original_ranks"
    ]
    uncertainty_scope: Literal[
        "conditional_on_fixed_heads_seeds_actions_anchors_queries_corruptions"
    ]
    required_reporting: tuple[str, ...]

    @model_validator(mode="after")
    def exact_analysis(self) -> V3Analysis:
        if self.metrics != ("top1", "mrr", "r_at_5") or self.bootstrap_cluster != (
            "setup",
            "performer",
            "repetition",
            "action",
        ):
            raise ValueError("v3 metrics and performance-group identity are fixed")
        if self.confirmatory_methods != (
            "contrastive",
            "contextual",
        ) or self.secondary_methods != ("supcon",):
            raise ValueError("v3 confirmatory and secondary roles are fixed")
        if self.required_reporting != (
            "clean_accuracy",
            "absolute_corrupted_accuracy",
            "every_seed",
            "every_corruption_curve",
            "leave_one_action_out",
            "fallback_frequency",
            "runtime",
            "memory",
            "failures",
        ):
            raise ValueError("v3 required reporting set is fixed")
        return self


class V3TestAccess(StrictModel):
    state: Literal["sealed"]
    final_evaluation_requires_lock: Literal[True]
    artifact_root_environment: Literal["POSE_EMBED_ARTIFACT_ROOT"]
    evaluation_plan_template: Literal["configs/evaluation-plan.v3.yaml"]
    protocol_lock_relative_path: Literal["study-v3/locks/protocol-lock.v3.json"]
    evaluation_plan_relative_path: Literal["study-v3/locks/evaluation-plan.v3.yaml"]
    final_run_set_relative_path: Literal["study-v3/locks/final-run-set.v3.json"]
    opening_ledger_relative_path: Literal["study-v3/locks/test-opening.v3.json"]
    design_lock_relative_path: Literal["study-v3/locks/design-lock.v3.json"]
    selection_authorization_relative_path: Literal[
        "study-v3/locks/selection-authorization.v3.json"
    ]
    resolved_protocol_relative_path: Literal["study-v3/locks/protocol.v3.json"]
    opening_policy: Literal["one_atomic_dataset_opening_across_all_protocol_versions"]
    training_after_opening: Literal["forbidden_across_all_protocol_versions"]
    confirmatory_changes_after_opening: Literal["forbidden"]


class ProtocolV3Config(StrictModel):
    schema_version: Literal[3]
    protocol_id: Literal["protocol-v3"]
    status: Literal["template", "resolved"]
    title: str
    timezone: Literal["America/New_York"]
    schedule: ScheduleConfig
    research_question: str
    dataset: DatasetConfig
    input_pipeline: InputPipelineConfig
    encoder: EncoderConfig
    batch: BatchConfig
    objectives: V3Objectives
    training: V3Training
    corruptions: V3Corruptions
    analysis: V3Analysis
    test_access: V3TestAccess
    provenance: V3Provenance
    preparation: V3Preparation | None

    @model_validator(mode="after")
    def exact_design(self) -> ProtocolV3Config:
        if (self.status == "resolved") != (self.preparation is not None):
            raise ValueError(
                "only a resolved v3 protocol has complete preparation bindings"
            )
        source = self.dataset.source_contract
        if (
            source.aggregate_relative_path != "ntu120_hrnet.pkl"
            or source.aggregate_bytes != 1238461428
            or source.aggregate_sha256
            != "aaf1f928b4629fa9a0850528d43fdd8d920532805d16672bfdda78085b649df8"
            or source.missing_list_relative_path
            != "provenance/sources/NTU_RGBD120_samples_with_missing_skeletons.txt"
            or source.missing_list_bytes != 11451
            or source.missing_list_sha256
            != "ab14fe64e89be63d2b08141713fcc31f6ebc7b01955009c3585d8d3367e0facc"
            or (source.missing_sample_count, source.nominal_capture_count)
            != (535, 114480)
            or self.dataset.official_protocol_source_commit
            != "ac2ebc87e6e9777ea6bac67e65e53b325b903f74"
        ):
            raise ValueError("v3 must retain the adopted physical source contract")
        if (
            self.dataset.novel_actions != tuple(range(1, 120, 6))
            or self.dataset.development_validation_actions != tuple(range(2, 120, 6))
            or not self.dataset.exclude_anchor_performance_views_from_primary_queries
            or (self.dataset.frames, self.dataset.joints) != (100, 17)
            or (
                self.encoder.representation_dimension,
                self.encoder.embedding_dimension,
                self.encoder.people,
            )
            != (512, 2048, 2)
            or (
                self.batch.classes_per_batch,
                self.batch.samples_per_class,
                self.batch.physical_batch_size,
            )
            != (8, 4, 32)
        ):
            raise ValueError(
                "v3 dataset identities, head, and physical batch are fixed"
            )
        return self


def validate_v3_experiment(
    experiment: ExperimentConfig, protocol: ProtocolV3Config
) -> None:
    """All arms share a grid; contextual retains its distinct published margin."""
    if experiment.objective not in protocol.objectives.core:
        raise ValueError("v3 excludes stretch/control objectives")
    if experiment.seed not in protocol.training.seeds:
        raise ValueError("v3 experiment seed is outside the fixed paired seeds")
    if (
        experiment.input_dimension,
        experiment.embedding_dimension,
        experiment.epochs,
        experiment.classes_per_batch,
        experiment.samples_per_class,
    ) != (8704, 2048, 20, 8, 4):
        raise ValueError("v3 dimensions, duration, and batch must match the protocol")
    if (
        TuningTrial(
            learning_rate=experiment.learning_rate, weight_decay=experiment.weight_decay
        )
        not in protocol.training.tuning_grid
    ):
        raise ValueError("v3 optimizer settings are outside the three-rate grid")
    recipe = (
        protocol.objectives.contextual
        if experiment.objective == "contextual"
        else protocol.objectives.contrastive
    )
    if (
        experiment.positive_margin,
        experiment.negative_margin,
        experiment.temperature,
    ) != (recipe.positive_margin, recipe.negative_margin, 0.07):
        raise ValueError("v3 experiment margins/temperature differ from its recipe")
    if experiment.objective == "contextual":
        assert experiment.contextual is not None
        for name, value in experiment.contextual.model_dump().items():
            if getattr(protocol.objectives.contextual, name) != value:
                raise ValueError(f"v3 contextual setting differs: {name}")
