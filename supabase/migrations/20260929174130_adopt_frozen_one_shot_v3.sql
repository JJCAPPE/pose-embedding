-- Adopt the final v3 public plan from the observed September 29 live predecessor.
-- Preserve Weeks 1-3, all actual time, completions, evidence, ownership and audit history.
-- Change future planning content only; every touched row is content/version guarded.
-- Empty databases import research-plan.v3.json through the administrative seed command.
-- The migration neither changes scientific configuration nor opens the novel test.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "projects",
    "id": "pose-embed",
    "week_id": null,
    "before": {
      "end_date": "2026-12-18",
      "id": "pose-embed",
      "plan_version": "1.0.0",
      "research_question": "Does contextual similarity learning improve motion retrieval relative to the full image-paper comparison roster, including Multi-Similarity with and without mining?",
      "slug": "pose-embed",
      "start_date": "2026-09-15",
      "summary": "A controlled motion-domain replication: contextual versus contrastive development first, followed by all 26 declared configurations with a common fine-tuned MotionBERT backbone. The current dates are a provisional planning horizon, subject to measured resources and complete method coverage.",
      "timezone": "America/New_York",
      "title": "Metric learning for human-motion retrieval",
      "version": 3,
      "visibility": "public"
    },
    "values": {
      "title": "Frozen one-shot pose robustness",
      "research_question": "Does the full contextual training recipe reduce one-shot retrieval degradation relative to a standard contrastive recipe when only novel pose queries are corrupted?",
      "summary": "Final v3 December study: frozen MotionBERT, three training recipes, three paired seeds, 20 epochs, and nine query-only corruption conditions. Three engineering pilots precede 27 selection runs, nine fresh final heads, and 180 locked evaluation cells. Implementation, measured capacity, and test-opening gates remain prerequisites; null or negative results are valid outcomes."
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-04",
    "week_id": "week-04",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-10-11",
      "id": "week-04",
      "number": 4,
      "objective": "Run Contextual and its contrastive component first on the same clean development problem, with the common fine-tuned backbone.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-10-05",
      "state": "planned",
      "title": "Priority pair on development",
      "version": 2
    },
    "values": {
      "phase": "Implementation and engineering",
      "title": "Verified recipes and full pilots",
      "objective": "Verify the three fixed recipes and the frozen-head path, then complete three full 20-epoch pilots under the immutable v3 design.",
      "deliverable": "Loss fixtures, paired initialization/batch evidence, fresh parity and clean caches, and three complete pilot records with timing and diagnostics.",
      "risks": [
        "The v3 protocol, shared seal checks and all cache-affecting code must be frozen before fresh extraction.",
        "A mathematical, nonfinite or collapse failure blocks selection; pilot accuracy cannot justify tuning recipes or duration."
      ],
      "advisor_prompt": "Do the mathematics, immutable inputs and complete pilot records demonstrate a valid fixed-budget comparison?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-10-18",
      "id": "week-05",
      "number": 5,
      "objective": "Implement the paper loss-comparison families under the shared encoder, head, sampler and development-selection budget.",
      "phase": "Motion replication v2",
      "planned_minutes": 300,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-10-12",
      "state": "planned",
      "title": "Published loss baselines",
      "version": 2
    },
    "values": {
      "phase": "Preselection go/no-go",
      "title": "Corruptions, analysis and capacity",
      "objective": "Complete every scientific and measured resource prerequisite for the October 18 selection decision.",
      "deliverable": "Nine verified development corruption paths, fixed analysis fixtures and an immutable go/no-go report against the unchanged v3 protocol digest.",
      "risks": [
        "The September 29 quota observation is 41.95 GB short of the initial storage requirement; new measurements and authorized capacity are required.",
        "The inherited time estimates do not establish available hours; full pipeline timings and an allocation calendar must support the deadline."
      ],
      "advisor_prompt": "Do all October 18 validity, seal, storage, runtime and researcher-availability criteria pass without changing the declared study?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-06",
    "week_id": "week-06",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-10-25",
      "id": "week-06",
      "number": 6,
      "objective": "Adapt every architecture-specific comparison to motion and document departures from the image design.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-10-19",
      "state": "planned",
      "title": "Architecture method adaptations",
      "version": 2
    },
    "values": {
      "phase": "Clean development selection",
      "title": "Launch the paired selection matrix",
      "objective": "Start the equal attempted budget of 27 fresh development runs after the October 18 authorization.",
      "deliverable": "Immutable attempts for three arms, three learning rates and three seeds, with clean epoch-20 development metrics.",
      "risks": [
        "A candidate requires three valid seeds; partial-seed averages cannot compete.",
        "Infrastructure retries preserve identical settings in new attempt directories and consume forecast capacity."
      ],
      "advisor_prompt": "Is every selection attempt authorized, paired, complete at 20 epochs and evaluated only on clean development data?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-07",
    "week_id": "week-07",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-11-01",
      "id": "week-07",
      "number": 7,
      "objective": "Establish all 26 configurations can run before expensive benchmark selection starts.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-10-26",
      "state": "planned",
      "title": "Complete coverage and resource gate",
      "version": 3
    },
    "values": {
      "phase": "Clean development selection",
      "title": "Complete selection and lock rates",
      "objective": "Finish all 27 declared selection attempts and lock one valid rate per arm using the exact ranking rule.",
      "deliverable": "A complete selection ledger and timestamped three-recipe selection decision by November 1.",
      "risks": [
        "A numerical failure makes a candidate ineligible until resolved; each selected candidate needs all three valid seeds.",
        "An arm with no valid candidate requires a result-blind amendment, not an alternate recipe or reduced seed count."
      ],
      "advisor_prompt": "Can an independent replay reproduce every selected rate from the complete unrounded clean development records?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-08",
    "week_id": "week-08",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-11-08",
      "id": "week-08",
      "number": 8,
      "objective": "Tune all declared configurations exclusively on the class-disjoint development split.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-11-02",
      "state": "planned",
      "title": "Equal-budget full-roster selection",
      "version": 2
    },
    "values": {
      "phase": "Fresh final training",
      "title": "Train the nine final heads",
      "objective": "Train the selected recipes from fresh paired initialization on all 100 auxiliary actions.",
      "deliverable": "Authorized final training attempts toward nine 20-epoch heads with immutable provenance and epoch-20 weights.",
      "risks": [
        "Development or pilot heads cannot be reused as final heads.",
        "Complete runs must fit approved allocations; partial attempts remain retained and cannot become resumable selection shortcuts."
      ],
      "advisor_prompt": "Are the final heads fresh, paired and bound to the selected clean-development recipes and all-auxiliary data?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-09",
    "week_id": "week-09",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-11-15",
      "id": "week-09",
      "number": 9,
      "objective": "Lock selection, retrieval manifests, statistics and the complete run roster before final retraining.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-11-09",
      "state": "planned",
      "title": "Freeze protocol and full final roster",
      "version": 2
    },
    "values": {
      "phase": "Fresh final training",
      "title": "Complete and verify final heads",
      "objective": "Finish and independently verify all nine final heads by November 15.",
      "deliverable": "Nine valid final checkpoints and complete final-run evidence ready for independent lock audit.",
      "risks": [
        "One missing or invalid required head blocks final opening.",
        "Corrections before opening require a dated result-blind decision and rerunning all affected comparisons."
      ],
      "advisor_prompt": "Are all nine heads complete, correctly paired and independently verifiable without any novel-data access?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-10",
    "week_id": "week-10",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-11-22",
      "id": "week-10",
      "number": 10,
      "objective": "Retrain all 26 locked configurations on all 100 auxiliary classes with six paired seeds.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-11-16",
      "state": "planned",
      "title": "Train every final configuration",
      "version": 2
    },
    "values": {
      "phase": "Independent audit and final locks",
      "title": "Audit the evaluator and final run set",
      "objective": "Independently validate final provenance, authorization and result completeness using development evidence.",
      "deliverable": "A reviewed final-run set, evaluator/analysis verification and report/figure templates prepared without novel outcomes.",
      "risks": [
        "Novel loader authorization must precede deserialization; shared dataset seals cannot be bypassed by legacy commands or namespaces.",
        "A changed protocol digest or cache-affecting defect invalidates affected artifacts and requires documented rework."
      ],
      "advisor_prompt": "Can the complete final campaign be authorized and reproduced without bypassing seal, identity or provenance checks?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-11",
    "week_id": "week-11",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-11-29",
      "id": "week-11",
      "number": 11,
      "objective": "Open the novel test once only after all 26 configurations and six seeds satisfy the complete lock.",
      "phase": "Motion replication v2",
      "planned_minutes": 240,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-11-23",
      "state": "planned",
      "title": "Open and evaluate the complete roster",
      "version": 2
    },
    "values": {
      "phase": "Independent audit and final locks",
      "title": "Finish locks and preserve recovery time",
      "objective": "Complete all final-head and lock audits by November 29 while preserving Thanksgiving as recovery time.",
      "deliverable": "A complete final authorization package and current capacity/seal evidence for the following week’s single novel campaign.",
      "risks": [
        "Reaching the date does not authorize opening; every final dependency and current resource check must pass.",
        "Thanksgiving is recovery capacity, not permission to compress or skip independent verification."
      ],
      "advisor_prompt": "Are all nine heads and every opening prerequisite verified, with sufficient current capacity for the complete campaign?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-12",
    "week_id": "week-12",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-12-06",
      "id": "week-12",
      "number": 12,
      "objective": "Compute the preregistered paired comparisons and regenerate complete results from immutable artifacts.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-11-30",
      "state": "planned",
      "title": "Analysis and independent reproduction",
      "version": 3
    },
    "values": {
      "phase": "Authorized novel evaluation",
      "title": "Open once and evaluate all 180 cells",
      "objective": "Run one fully authorized novel extraction and evaluation campaign by December 6.",
      "deliverable": "All 180 unique finite provenance-valid result cells and locked per-query ranks, with every operational attempt retained.",
      "risks": [
        "Opening is irreversible: a failed process does not reseal data or permit new training and selection.",
        "Missing or invalid cells block a complete report; post-opening corrections require explicit deviation reporting."
      ],
      "advisor_prompt": "Does every required final cell reproduce from the same authorized source, opening, protocol, caches and checkpoint set?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-13",
    "week_id": "week-13",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-12-13",
      "id": "week-13",
      "number": 13,
      "objective": "Present the motion replication with complete provenance and explicit differences from the image paper.",
      "phase": "Motion replication v2",
      "planned_minutes": 480,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-12-07",
      "state": "planned",
      "title": "Report and evidence package",
      "version": 3
    },
    "values": {
      "phase": "Analysis and communication",
      "title": "Analyze and report the declared study",
      "objective": "Produce the conditional primary analysis and complete descriptive report with accurate recipe-level claims.",
      "deliverable": "Reproducible conditional interval, absolute accuracy/degradation curves, seed/cell/action sensitivities, resource tables and report/poster draft.",
      "risks": [
        "Less degradation can coexist with lower absolute corrupted accuracy; both must be reported.",
        "The interval is conditional on fixed heads, seeds, actions, anchors and corruptions, and cannot support universal robustness or a contextual-term-only causal claim."
      ],
      "advisor_prompt": "Do the claims follow the single prespecified interval rule while showing absolute performance, uncertainty limits and all required descriptive results?"
    },
    "operation": "update"
  },
  {
    "table": "weeks",
    "id": "week-14",
    "week_id": "week-14",
    "before": {
      "actual_minutes": 0,
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?",
      "closed_at": null,
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "end_date": "2026-12-18",
      "id": "week-14",
      "number": 14,
      "objective": "Finish the verified study or explicitly carry unfinished required work beyond this provisional horizon.",
      "phase": "Motion replication v2",
      "planned_minutes": 240,
      "project_id": "pose-embed",
      "reflection": "",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "start_date": "2026-12-14",
      "state": "planned",
      "title": "Archive or document continuation",
      "version": 2
    },
    "values": {
      "phase": "Delivery and archive",
      "title": "Deliver and archive the December study",
      "objective": "Deliver the final report/poster and recoverable permitted evidence by December 18.",
      "deliverable": "Final report/poster, independent reproduction smoke test, public-safe archive and reconciled tracker; if blocked, an explicit incomplete-study record.",
      "risks": [
        "Licensed data, checkpoints, caches, full artifacts and private governance records must remain outside Git and public exports.",
        "A blocked or incomplete campaign cannot be presented as a completed empirical comparison."
      ],
      "advisor_prompt": "Can a reader reproduce every permitted result and distinguish completed evidence, limitations and any unresolved work?"
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w04-task-01",
    "week_id": "week-04",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Record source-paper mapping, all 26 configurations, common settings and explicit unresolved blockers.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Record source-paper mapping, all 26 configurations, common settings and explicit unresolved blockers.",
      "id": "w04-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Adopt the v2 amendment and method registry",
      "version": 2,
      "week_id": "week-04"
    },
    "values": {
      "title": "Freeze and validate the v3 path",
      "details": "Complete explicit v3 configuration/manifest validation, dataset-wide seal checks and auxiliary/novel source access separation. Register historical roots, preserve old artifacts, and freeze the complete design and cache-affecting code before extraction.",
      "expected_output": "An immutable v3 design/pilot specification and passing version, provenance and seal checks."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w04-task-02",
    "week_id": "week-04",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Use independent paper-faithful Contextual and exact contrastive component, finite gradient/reference tests, and common fine-tuned MotionBERT.",
      "estimate_minutes": 180,
      "evidence_url": null,
      "expected_output": "Use independent paper-faithful Contextual and exact contrastive component, finite gradient/reference tests, and common fine-tuned MotionBERT.",
      "id": "w04-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Implement the priority two-method path",
      "version": 2,
      "week_id": "week-04"
    },
    "values": {
      "title": "Verify losses and paired training",
      "details": "Check independent labeled forward/backward fixtures, the physical 8 × 4 sampler and shared initialization. Run the constructed 32-row learnable fixture for 1,000 updates per arm; require finite training and 100% self-excluded same-label retrieval.",
      "expected_output": "Verified three-arm numerical behavior and paired initialization/batch hashes."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w04-task-03",
    "week_id": "week-04",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Run both methods from identical initialization and batch plan; retain every attempt and six-seed pairing design without touching novel data.",
      "estimate_minutes": 120,
      "evidence_url": null,
      "expected_output": "Run both methods from identical initialization and batch plan; retain every attempt and six-seed pairing design without touching novel data.",
      "id": "w04-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Run paired development smoke and overfit checks",
      "version": 2,
      "week_id": "week-04"
    },
    "values": {
      "title": "Generate fresh frozen features",
      "details": "Create v3-bound manifests with unchanged sample identities; run encoder parity and two fresh-process all-auxiliary extractions on the same GPU. Retain both repeats and development train/gallery/query caches with hashes.",
      "expected_output": "Fresh v3 parity/repeatability evidence and five immutable clean feature caches."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w04-task-04",
    "week_id": "week-04",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Measure real forward/backward time, memory and storage; forecast 156 final runs plus selection trials and revise provisional dates.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Measure real forward/backward time, memory and storage; forecast 156 final runs plus selection trials and revise provisional dates.",
      "id": "w04-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Measure feasibility before broadening",
      "version": 2,
      "week_id": "week-04"
    },
    "values": {
      "title": "Run three complete engineering pilots",
      "details": "Run Contrastive, Contextual and SupCon for 20 epochs at seed 7 and rate 3e-4. Preserve epoch-5/10/15/20 checkpoints and complete clean scores plus epoch-zero diagnostics, finite/collapse checks and measured timing/memory/bytes.",
      "expected_output": "Three valid full pilots, ineligible for learning-rate selection, with complete diagnostic evidence."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w05-task-01",
    "week_id": "week-05",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Implement Triplet, MS, MS + miner and NT-Xent with exact distance, normalization and mining semantics.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Implement Triplet, MS, MS + miner and NT-Xent with exact distance, normalization and mining semantics.",
      "id": "w05-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Implement pair and triplet losses",
      "version": 2,
      "week_id": "week-05"
    },
    "values": {
      "title": "Audit nested corruptions and fallback",
      "details": "Verify shared jitter fields, nested joint/frame masks, exact missingness and severity-zero identity on a fixed development panel. Freeze the training-only torso fallback and report its source IDs, value and effective damage evidence.",
      "expected_output": "A deterministic geometry audit and bound fallback evidence for all nine conditions."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Implement Proxy Anchor, Proxy NCA, Proxy NCA++ and normalized softmax with documented proxy learning rates and initialization.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Implement Proxy Anchor, Proxy NCA, Proxy NCA++ and normalized softmax with documented proxy learning rates and initialization.",
      "id": "w05-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Implement proxy and classification losses",
      "version": 2,
      "week_id": "week-05"
    },
    "values": {
      "title": "Complete full development corruption paths",
      "details": "Run all nine full-size development query paths and retain artifacts. Time maximum severity per family through provenance checks, preprocessing, encoding, storage, projection of all three pilot heads and retrieval. Scores cannot select recipes or settings.",
      "expected_output": "Complete identities/invariants for nine conditions and measured end-to-end family timings."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w05-task-03",
    "week_id": "week-05",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Implement ROADMAP, FastAP, SmoothAP and SupCon from permitted sources; record any blocked dependency explicitly.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Implement ROADMAP, FastAP, SmoothAP and SupCon from permitted sources; record any blocked dependency explicitly.",
      "id": "w05-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Implement ranking losses and SupCon",
      "version": 3,
      "week_id": "week-05"
    },
    "values": {
      "title": "Verify the fixed analysis",
      "details": "Use hand-ranked and unequal-view fixtures to verify query weighting, within-action performance-cluster draws, fixed seeds, percentile intervals and leave-one-action-out with an unchanged gallery. Freeze analysis code before selection.",
      "expected_output": "Reproducible metric and conditional-bootstrap fixtures bound to the v3 analysis."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Check values/gradients, edge cases, short development overfits, licenses and registry status for all loss-only methods.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Check values/gradients, edge cases, short development overfits, licenses and registry status for all loss-only methods.",
      "id": "w05-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Verify every loss configuration",
      "version": 2,
      "week_id": "week-05"
    },
    "values": {
      "title": "Record the October 18 go/no-go",
      "details": "Combine valid pilots, seal audits and full pipeline timing with final-size memory evidence, an allocation calendar and researcher-confirmed hours. Require available bytes ≥ 200 × 2^30 + 1.25 × remaining peak bytes; apply at least 25% work slack plus queue/setup time. Resolve the initial 41.95 GB gap and append selection authorization against the unchanged digest, or stop for an amendment.",
      "expected_output": "A measured capacity/availability report and explicit pass or documented blocked-study amendment."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w06-task-01",
    "week_id": "week-06",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Specify and implement required distribution, local alignment and disentangled branches using compatible motion features.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Specify and implement required distribution, local alignment and disentangled branches using compatible motion features.",
      "id": "w06-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Adapt DRML, DIML and DiVA",
      "version": 2,
      "week_id": "week-06"
    },
    "values": {
      "title": "Verify selection authorization",
      "details": "Check the unchanged v3 digest, complete pilot/corruption/analysis evidence, historical seal audit and measured capacity decision before the first selection job.",
      "expected_output": "A verified immutable selection authorization and exact 27-run attempt matrix."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w06-task-02",
    "week_id": "week-06",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Implement their required training mechanisms, auxiliaries and supervision, with permitted provenance.",
      "estimate_minutes": 300,
      "evidence_url": null,
      "expected_output": "Implement their required training mechanisms, auxiliaries and supervision, with permitted provenance.",
      "id": "w06-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Adapt IBC and S2SD",
      "version": 2,
      "week_id": "week-06"
    },
    "values": {
      "title": "Run the first selection allocations",
      "details": "Schedule fresh 20-epoch runs for each arm at 1e-4, 3e-4 and 1e-3 with seeds 7, 17 and 29. Reuse paired initialization and physical batch plans within each seed; respect measured GPU, memory, wall-time and storage limits.",
      "expected_output": "Completed authorized selection attempts with paired hashes and epoch-20 checkpoints."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w06-task-03",
    "week_id": "week-06",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Preserve method-specific mixing, relation, hierarchy and graph mechanisms; generic scalar substitutes are prohibited.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Preserve method-specific mixing, relation, hierarchy and graph mechanisms; generic scalar substitutes are prohibited.",
      "id": "w06-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Adapt all Metrix variants, HIST and MHGL",
      "version": 2,
      "week_id": "week-06"
    },
    "values": {
      "title": "Score clean development endpoints",
      "details": "Evaluate complete clean development top-1 and MRR at epoch 20 with the fixed gallery/query lists and tie order. Exclude pilot weights and corrupted scores from ranking.",
      "expected_output": "Unrounded clean endpoint metrics with checkpoint and input provenance."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w06-task-04",
    "week_id": "week-06",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Implement PA + AVSL and Contextual at 1,536 dimensions; document identical dimensions/backbone budgets and architecture costs.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Implement PA + AVSL and Contextual at 1,536 dimensions; document identical dimensions/backbone budgets and architecture costs.",
      "id": "w06-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Implement the matched AVSL comparison",
      "version": 2,
      "week_id": "week-06"
    },
    "values": {
      "title": "Maintain the attempt and capacity ledger",
      "details": "Retain successes, partial outputs and failures. Retry only identical infrastructure-failed attempts from scratch; record updated measured bytes and remaining-work forecasts.",
      "expected_output": "A current immutable attempt ledger with all failures and current capacity checks."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w07-task-01",
    "week_id": "week-07",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Reconcile main tables and appendix, reproducibility scope, equations, licenses and all 26 registry entries.",
      "estimate_minutes": 240,
      "evidence_url": null,
      "expected_output": "Reconcile main tables and appendix, reproducibility scope, equations, licenses and all 26 registry entries.",
      "id": "w07-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Audit the complete paper mapping",
      "version": 2,
      "week_id": "week-07"
    },
    "values": {
      "title": "Finish the declared selection matrix",
      "details": "Complete and account for every arm × rate × seed attempt at 20 epochs. Preserve all numerical failures and identical infrastructure retries; never silently omit a setting or replace its budget.",
      "expected_output": "A complete 27-setting attempt ledger with valid-run and failure status."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w07-task-02",
    "week_id": "week-07",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Require finite training and retrieval output for every configuration with fixed development data.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Require finite training and retrieval output for every configuration with fixed development data.",
      "id": "w07-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Run all-method development smoke matrix",
      "version": 2,
      "week_id": "week-07"
    },
    "values": {
      "title": "Reproduce candidate ranking",
      "details": "Within each arm rank eligible three-seed candidates by mean epoch-20 clean top-1, then mean MRR, then lower learning rate, using unrounded metrics. Report unequal numbers of eligible candidates.",
      "expected_output": "An independently reproducible candidate table with tie and eligibility decisions."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w07-task-03",
    "week_id": "week-07",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Use measured backward memory across methods; publish equal selection budgets and method-specific grids.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Use measured backward memory across methods; publish equal selection budgets and method-specific grids.",
      "id": "w07-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Freeze physical batches and trial budget",
      "version": 2,
      "week_id": "week-07"
    },
    "values": {
      "title": "Lock the selected configurations",
      "details": "Bind the three selected rates, full evidence, attempt provenance and timestamp to the unchanged protocol. If any arm has no valid candidate, stop and document the amendment.",
      "expected_output": "A timestamped selection lock for all three recipes, or an explicit blocker."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w07-task-04",
    "week_id": "week-07",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Measure time/storage and researcher work, and record continuation dates if the December planning horizon is insufficient.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Measure time/storage and researcher work, and record continuation dates if the December planning horizon is insufficient.",
      "id": "w07-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Reforecast the full study",
      "version": 2,
      "week_id": "week-07"
    },
    "values": {
      "title": "Prepare all-auxiliary final training",
      "details": "Verify the fresh 95,001-row v3 cache and generate paired all-100-action batch plans and initial states for seeds 7, 17 and 29. Recheck capacity and complete-run allocation limits.",
      "expected_output": "Nine fresh final-run specifications and updated capacity evidence."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w08-task-01",
    "week_id": "week-08",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Declare each method trial space, budget, checkpoint rule and tie-break before trials.",
      "estimate_minutes": 300,
      "evidence_url": null,
      "expected_output": "Declare each method trial space, budget, checkpoint rule and tie-break before trials.",
      "id": "w08-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Freeze the tuning ledger",
      "version": 2,
      "week_id": "week-08"
    },
    "values": {
      "title": "Validate all-auxiliary inputs",
      "details": "Revalidate source/checkpoint hashes, all 95,001 sample identities, fresh cache sidecars and locked selected rates before final training.",
      "expected_output": "A verified final-input and configuration manifest."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w08-task-02",
    "week_id": "week-08",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Execute every budgeted trial and preserve attempts, outcomes and per-method resource use.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Execute every budgeted trial and preserve attempts, outcomes and per-method resource use.",
      "id": "w08-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Run the complete development matrix",
      "version": 2,
      "week_id": "week-08"
    },
    "values": {
      "title": "Train paired final recipes",
      "details": "Run Contrastive, Contextual and SupCon for 20 epochs with seeds 7, 17 and 29 on all 100 auxiliary actions. Pair head initialization and physical batch plans; retain only the prescribed epoch-20 final choice.",
      "expected_output": "Immutable final attempts with exact 59,380 updates per complete head."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w08-task-03",
    "week_id": "week-08",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Use six paired seeds under the declared selection design; account for early engineering trials transparently.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Use six paired seeds under the declared selection design; account for early engineering trials transparently.",
      "id": "w08-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Replicate candidates across paired seeds",
      "version": 2,
      "week_id": "week-08"
    },
    "values": {
      "title": "Record final health and cost",
      "details": "Preserve finite-parameter checks, normalization diagnostics, timing, memory, saved bytes, initialization/batch hashes and the complete attempt history. Do not inspect novel inputs or outcomes.",
      "expected_output": "Per-head health, pairing, cost and provenance records."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w08-task-04",
    "week_id": "week-08",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Classify operational failures and scientific instability, reconcile budgets, and document all deviations.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Classify operational failures and scientific instability, reconcile budgets, and document all deviations.",
      "id": "w08-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Audit failures and fairness",
      "version": 2,
      "week_id": "week-08"
    },
    "values": {
      "title": "Review remaining final workload",
      "details": "Track remaining heads against the measured allocation calendar and capacity formula, retaining failed outputs and at least 25% remaining-work slack.",
      "expected_output": "An updated remaining-work forecast that preserves the final-lock deadline."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w09-task-01",
    "week_id": "week-09",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Bind multi-positive held-out manifests, relevant counts, self/synchronized exclusions, ties and aggregation.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Bind multi-positive held-out manifests, relevant counts, self/synchronized exclusions, ties and aggregation.",
      "id": "w09-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Freeze the primary retrieval protocol",
      "version": 2,
      "week_id": "week-09"
    },
    "values": {
      "title": "Complete remaining final attempts",
      "details": "Finish all three recipes × three seeds on all 95,001 auxiliary rows. Retain every prior attempt and restart infrastructure failures only with identical inputs and settings.",
      "expected_output": "All nine complete 20-epoch final heads or a visible blocker."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w09-task-02",
    "week_id": "week-09",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Record paired interval construction, multiplicity treatment, one-shot and any corruption/ablation scope before outcomes.",
      "estimate_minutes": 240,
      "evidence_url": null,
      "expected_output": "Record paired interval construction, multiplicity treatment, one-shot and any corruption/ablation scope before outcomes.",
      "id": "w09-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Freeze statistics and supplementary analyses",
      "version": 2,
      "week_id": "week-09"
    },
    "values": {
      "title": "Audit checkpoint and manifest integrity",
      "details": "Verify every checkpoint hash, source/input contract, protocol/config/code/dependency binding, paired initialization/batches and exact update count. Confirm pilot and development heads are absent from the final set.",
      "expected_output": "A complete nine-head integrity and provenance report."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w09-task-03",
    "week_id": "week-09",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Bind 26 selected configurations, initializations, physical batches, augmentation and dependency/source hashes.",
      "estimate_minutes": 120,
      "evidence_url": null,
      "expected_output": "Bind 26 selected configurations, initializations, physical batches, augmentation and dependency/source hashes.",
      "id": "w09-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Lock all method settings and six seeds",
      "version": 2,
      "week_id": "week-09"
    },
    "values": {
      "title": "Build the final evaluation manifest",
      "details": "Freeze clean gallery order and exact primary/exact-official query lists from metadata. Declare all three methods × three seeds × ten conditions × two query definitions and every expected artifact role.",
      "expected_output": "A fixed 180-cell evaluation matrix with exact ordered identities and role contracts."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w09-task-04",
    "week_id": "week-09",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Prove an incomplete final roster cannot open the test; final lock must await every required final checkpoint.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Prove an incomplete final roster cannot open the test; final lock must await every required final checkpoint.",
      "id": "w09-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Verify no final-test authorization yet",
      "version": 2,
      "week_id": "week-09"
    },
    "values": {
      "title": "Confirm the audit schedule",
      "details": "Reserve November 16-29 for independent evaluator/run-set/lock checks, report templates and recovery. Update allocation and storage forecasts before any opening decision.",
      "expected_output": "A feasible final-audit and evaluation calendar with recorded capacity evidence."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w10-task-01",
    "week_id": "week-10",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Complete 26 configurations by six seeds using locked settings; retain every immutable attempt.",
      "estimate_minutes": 150,
      "evidence_url": null,
      "expected_output": "Complete 26 configurations by six seeds using locked settings; retain every immutable attempt.",
      "id": "w10-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Execute the 156 final runs",
      "version": 2,
      "week_id": "week-10"
    },
    "values": {
      "title": "Audit the evaluator end to end",
      "details": "Verify hand-ranked metrics, deterministic ties, both query definitions, cache subset identity, all-head projection and the expected 180-cell completeness rules using permitted fixtures and development data.",
      "expected_output": "An independent evaluator and completeness-verifier report."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w10-task-02",
    "week_id": "week-10",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Validate weights, optimizer settings, batches, initialization and code against selected configurations.",
      "estimate_minutes": 120,
      "evidence_url": null,
      "expected_output": "Validate weights, optimizer settings, batches, initialization and code against selected configurations.",
      "id": "w10-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Verify checkpoint and run provenance",
      "version": 2,
      "week_id": "week-10"
    },
    "values": {
      "title": "Verify dataset-wide opening controls",
      "details": "Test cross-version denial, historical-root audit resolution, authorization before novel loading, concurrent first-opening behavior and fail-closed recovery of partial opening transactions.",
      "expected_output": "Passing v1/v2/v3 seal and first-opening safety checks."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w10-task-03",
    "week_id": "week-10",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Retry only documented operational failures in new directories without changing scientific parameters.",
      "estimate_minutes": 150,
      "evidence_url": null,
      "expected_output": "Retry only documented operational failures in new directories without changing scientific parameters.",
      "id": "w10-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Apply the declared failure policy",
      "version": 2,
      "week_id": "week-10"
    },
    "values": {
      "title": "Audit and assemble final locks",
      "details": "Cross-check nine final heads, selected settings, exact IDs, source/checkpoint/input hashes, code/dependency hashes and the evaluation plan before recording the researcher-controlled final lock.",
      "expected_output": "An independently checked complete final-run set and staged final-lock evidence."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w10-task-04",
    "week_id": "week-10",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Bind every required checkpoint and manifest only after all final training is finished.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Bind every required checkpoint and manifest only after all final training is finished.",
      "id": "w10-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Complete the full final-run lock",
      "version": 2,
      "week_id": "week-10"
    },
    "values": {
      "title": "Prepare report and figure templates",
      "details": "Rehearse clean/corrupted accuracy, degradation, conditional intervals, seed/cell/leave-one-action-out tables and costs from development or fixture records. Mark examples as non-final.",
      "expected_output": "Reproducible report/figure templates ready for locked final results."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w11-task-01",
    "week_id": "week-11",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Cross-check methods, seeds, runs, gallery/query construction, sources, code and statistical-plan hashes.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Cross-check methods, seeds, runs, gallery/query construction, sources, code and statistical-plan hashes.",
      "id": "w11-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Verify the full test-opening lock",
      "version": 2,
      "week_id": "week-11"
    },
    "values": {
      "title": "Resolve pre-opening audit findings",
      "details": "Correct verified pre-opening defects through documented result-blind decisions, rerunning all affected artifacts/comparisons where required. Preserve superseded evidence.",
      "expected_output": "An audit ledger with no unresolved final-opening blocker."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w11-task-02",
    "week_id": "week-11",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Produce the complete 26-by-six multi-positive retrieval matrix and per-query evidence.",
      "estimate_minutes": 120,
      "evidence_url": null,
      "expected_output": "Produce the complete 26-by-six multi-positive retrieval matrix and per-query evidence.",
      "id": "w11-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Evaluate all clean primary cells",
      "version": 2,
      "week_id": "week-11"
    },
    "values": {
      "title": "Complete final locks by November 29",
      "details": "Bind the nine checkpoints/run manifests, selected configurations, exact gallery/query lists, evaluation plan and source/protocol/code dependencies in the complete final lock. Confirm no scientific training remains active.",
      "expected_output": "The complete immutable final lock and final-run-set record."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w11-task-03",
    "week_id": "week-11",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Run only predeclared one-shot, corruption, frozen or ablation analyses; preserve their distinct status.",
      "estimate_minutes": 30,
      "evidence_url": null,
      "expected_output": "Run only predeclared one-shot, corruption, frozen or ablation analyses; preserve their distinct status.",
      "id": "w11-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Evaluate locked supplementary tasks",
      "version": 2,
      "week_id": "week-11"
    },
    "values": {
      "title": "Repeat seal and capacity audits",
      "details": "Recheck every registered historical root and release, filesystem/quota limits, forecast remaining peak bytes, allocation and opening recovery procedure. A missing or unreadable root blocks opening.",
      "expected_output": "Current resolved seal and capacity reports for the authorized source."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w11-task-04",
    "week_id": "week-11",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Audit exact matrix coverage, identical query eligibility and dimension grouping without post-test tuning.",
      "estimate_minutes": 30,
      "evidence_url": null,
      "expected_output": "Audit exact matrix coverage, identical query eligibility and dimension grouping without post-test tuning.",
      "id": "w11-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Freeze all results and failure records",
      "version": 2,
      "week_id": "week-11"
    },
    "values": {
      "title": "Preserve recovery and handoff readiness",
      "details": "Use the reduced Thanksgiving work budget for required recovery and rehearse the authorized campaign checklist. If prerequisites cannot pass, keep the seal and record a dated blocker/amendment.",
      "expected_output": "A ready or explicitly blocked evaluation handoff with no invented completion."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w12-task-01",
    "week_id": "week-12",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Report Contextual versus Contrastive first, then all declared comparators with the frozen multiplicity rule.",
      "estimate_minutes": 120,
      "evidence_url": null,
      "expected_output": "Report Contextual versus Contrastive first, then all declared comparators with the frozen multiplicity rule.",
      "id": "w12-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Compute primary and broad paired comparisons",
      "version": 2,
      "week_id": "week-12"
    },
    "values": {
      "title": "Validate and atomically authorize opening",
      "details": "Revalidate all lock bindings and prior ledgers, confirm no training is active, and recheck capacity. Atomically record the shared dataset opening and v3 authorization before invoking the novel annotation loader.",
      "expected_output": "One immutable dataset-opening event bound to the complete v3 final lock."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w12-task-02",
    "week_id": "week-12",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Publish R@1/2/4/8, mAP, mAP@R, six-seed variation, failures and compute within each dimension group.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Publish R@1/2/4/8, mAP, mAP@R, six-seed variation, failures and compute within each dimension group.",
      "id": "w12-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Report every metric and resource cost",
      "version": 2,
      "week_id": "week-12"
    },
    "values": {
      "title": "Extract the final novel conditions",
      "details": "Encode one clean gallery and the novel query union for clean plus nine corruptions. Export two immutable role-specific query caches per condition and verify that primary rows are the exact ordered subset of exact-official rows.",
      "expected_output": "Authorized deterministic caches for both query definitions with complete corruption and source provenance."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w12-task-03",
    "week_id": "week-12",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Verify environment, source records and immutable artifact hashes independently.",
      "estimate_minutes": 120,
      "evidence_url": null,
      "expected_output": "Verify environment, source records and immutable artifact hashes independently.",
      "id": "w12-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Reproduce tables from a clean checkout",
      "version": 2,
      "week_id": "week-12"
    },
    "values": {
      "title": "Evaluate all heads and cells",
      "details": "Apply all nine final heads to the clean gallery and every query role/condition. Produce top-1, MRR, R@5 and per-query ranks for three methods × three seeds × ten conditions × two query definitions.",
      "expected_output": "180 unique finite result cells and their checkpoint-bound per-query evidence."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w12-task-04",
    "week_id": "week-12",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Describe positive, null or negative results and motion-adaptation limitations without universal claims.",
      "estimate_minutes": 150,
      "evidence_url": null,
      "expected_output": "Describe positive, null or negative results and motion-adaptation limitations without universal claims.",
      "id": "w12-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Write evidence-matched findings",
      "version": 3,
      "week_id": "week-12"
    },
    "values": {
      "title": "Verify campaign completeness",
      "details": "Independently regenerate cell metrics from ranks, validate every cross-binding and retain all failures/retries. Retry only the identical authorized operations; preserve any post-opening defect as a disclosed limitation.",
      "expected_output": "A complete final evaluation audit or an explicit incomplete/deviation record."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w13-task-01",
    "week_id": "week-13",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Map every image-paper method to its motion adaptation, source and evidence.",
      "estimate_minutes": 180,
      "evidence_url": null,
      "expected_output": "Map every image-paper method to its motion adaptation, source and evidence.",
      "id": "w13-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Write the full replication report",
      "version": 3,
      "week_id": "week-13"
    },
    "values": {
      "title": "Compute the locked primary analysis",
      "details": "Run 10,000 within-action performance-cluster bootstrap replicates with fixed seeds/actions and query-weighted multiplicities. Report Delta and its 95% percentile interval; claim smaller degradation only if the upper bound is below zero.",
      "expected_output": "A reproducible conditional primary estimate/interval and positive, null or contrary conclusion."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w13-task-02",
    "week_id": "week-13",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Correct reproducibility or presentation defects without adding outcome-driven analyses.",
      "estimate_minutes": 120,
      "evidence_url": null,
      "expected_output": "Correct reproducibility or presentation defects without adding outcome-driven analyses.",
      "id": "w13-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Resolve documented review findings",
      "version": 3,
      "week_id": "week-13"
    },
    "values": {
      "title": "Publish complete descriptive results",
      "details": "Show clean and absolute corrupted accuracy, Contextual-minus-Contrastive corrupted differences, every seed/cell effect, SupCon, exact-official results and 20 leave-one-action-out sensitivities with a fixed gallery.",
      "expected_output": "All prespecified tables and curves, including sign changes and conditional limits."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w13-task-03",
    "week_id": "week-13",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Explain the question, full comparison, uncertainty and limits clearly.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Explain the question, full comparison, uncertainty and limits clearly.",
      "id": "w13-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Prepare poster or slides",
      "version": 2,
      "week_id": "week-13"
    },
    "values": {
      "title": "Write the report and poster",
      "details": "Explain the frozen encoder, fixed transfer recipes, nested synthetic corruptions, selection, test seal, resource costs and retained failures. State that margins/regularization are part of the recipe and that v3 does not complete the v2 benchmark.",
      "expected_output": "A report/poster draft with claims traceable to locked evidence and honest scope limits."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w13-task-04",
    "week_id": "week-13",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Include source, configs, manifests, compact results and instructions while excluding licensed inputs and checkpoints.",
      "estimate_minutes": 90,
      "evidence_url": null,
      "expected_output": "Include source, configs, manifests, compact results and instructions while excluding licensed inputs and checkpoints.",
      "id": "w13-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Package permitted reproduction material",
      "version": 3,
      "week_id": "week-13"
    },
    "values": {
      "title": "Regenerate figures and resolve review findings",
      "details": "Reproduce every table and figure from immutable ranks/manifests, resolve presentation/reproducibility defects and explicitly label any post-opening scientific deviation.",
      "expected_output": "A reviewed reproduction log and permitted compact final evidence package."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w14-task-01",
    "week_id": "week-14",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Use the 26-configuration coverage ledger; missing methods or final runs remain incomplete.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Use the 26-configuration coverage ledger; missing methods or final runs remain incomplete.",
      "id": "w14-task-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Assess completion against full scope",
      "version": 2,
      "week_id": "week-14"
    },
    "values": {
      "title": "Run the independent reproduction smoke test",
      "details": "Reproduce permitted summaries and report outputs from the locked evidence, verify artifact references and document software/hardware requirements and operational limitations.",
      "expected_output": "An independent reproduction record for the final deliverables."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w14-task-02",
    "week_id": "week-14",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Extend the plan with measured estimates before opening the test if required work exceeds this horizon.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Extend the plan with measured estimates before opening the test if required work exceeds this horizon.",
      "id": "w14-task-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Record a dated continuation if needed",
      "version": 2,
      "week_id": "week-14"
    },
    "values": {
      "title": "Finalize the report and poster",
      "details": "Deliver the December report/poster with the full primary/descriptive results, recipe-level interpretation, conditional uncertainty, failures, costs and limitations. If the campaign is blocked, state the missing evidence and amendment explicitly.",
      "expected_output": "Final report/poster or an honest dated blocked-study report."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w14-task-03",
    "week_id": "week-14",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Preserve releases, histories, run manifests and compact outputs without overwriting prior artifacts.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Preserve releases, histories, run manifests and compact outputs without overwriting prior artifacts.",
      "id": "w14-task-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Archive source and permitted evidence",
      "version": 2,
      "week_id": "week-14"
    },
    "values": {
      "title": "Archive permitted material",
      "details": "Preserve source, versioned configs, manifests, compact summaries, license notices and reproduction instructions. Keep historical artifacts recoverable without overwriting them and exclude licensed/private material from Git.",
      "expected_output": "A recoverable license-safe release and evidence index."
    },
    "operation": "update"
  },
  {
    "table": "tasks",
    "id": "w14-task-04",
    "week_id": "week-14",
    "before": {
      "completed_at": null,
      "completion_note": "",
      "details": "Produce public-safe exports, check live protocol/schedule consistency and record actual researcher time.",
      "estimate_minutes": 60,
      "evidence_url": null,
      "expected_output": "Produce public-safe exports, check live protocol/schedule consistency and record actual researcher time.",
      "id": "w14-task-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "todo",
      "title": "Export and verify the tracker",
      "version": 2,
      "week_id": "week-14"
    },
    "values": {
      "title": "Reconcile and export the tracker",
      "details": "Verify live website, fallback, protocol and schedule consistency; preserve hosted evidence/versions and closed-week history. Record actual time only when supplied by the researcher and export only public-safe fields.",
      "expected_output": "A verified public tracker/export and researcher-supplied retrospective/time record where available."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w04-gate-01",
    "week_id": "week-04",
    "before": {
      "criterion": "Both priority methods pass independent value/gradient and common-debug-set checks.",
      "decided_at": null,
      "evidence": "",
      "id": "w04-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-04"
    },
    "values": {
      "criterion": "The complete v3 design and cache-affecting release are frozen; source identities are preserved and historical seal audits are resolved."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w04-gate-02",
    "week_id": "week-04",
    "before": {
      "criterion": "No novel-test data or score was loaded; paired initialization, batches and development provenance are complete.",
      "decided_at": null,
      "evidence": "",
      "id": "w04-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-04"
    },
    "values": {
      "criterion": "All three losses pass independent numerical and learnable-fixture checks; initialization and physical batch plans pair exactly."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w04-gate-03",
    "week_id": "week-04",
    "before": {
      "criterion": "The measured resource forecast and researcher workload decision determine the next schedule; v1 frozen-forward memory is not reused as fine-tuning evidence.",
      "decided_at": null,
      "evidence": "",
      "id": "w04-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-04"
    },
    "values": {
      "criterion": "Fresh parity/repeatability checks and all three 20-epoch pilots pass with four immutable checkpoint/score records each."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w05-gate-01",
    "week_id": "week-05",
    "before": {
      "criterion": "Every declared loss method has an auditable source, explicit parameters and passing numerical tests.",
      "decided_at": null,
      "evidence": "",
      "id": "w05-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-05"
    },
    "values": {
      "criterion": "All nine development conditions pass nesting, fallback, identity, deterministic-output and full pipeline checks."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w05-gate-02",
    "week_id": "week-05",
    "before": {
      "criterion": "The same physical batch and 512-dimensional head are used where scientifically applicable.",
      "decided_at": null,
      "evidence": "",
      "id": "w05-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-05"
    },
    "values": {
      "criterion": "The predeclared conditional analysis is tested; all three pilots and historical seal audits remain valid under the unchanged protocol digest."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "before": {
      "criterion": "Unavailable implementations remain required blockers and are not silently removed.",
      "decided_at": null,
      "evidence": "",
      "id": "w05-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 3,
      "waiver_reason": "",
      "week_id": "week-05"
    },
    "values": {
      "criterion": "The October 18 schedule, storage and availability report passes and authorizes selection; otherwise no sweep starts."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w06-gate-01",
    "week_id": "week-06",
    "before": {
      "criterion": "Every architecture row is implemented faithfully or remains an explicit blocker with an adaptation decision.",
      "decided_at": null,
      "evidence": "",
      "id": "w06-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-06"
    },
    "values": {
      "criterion": "All launched runs match the declared matrix and use paired seeds, initialization and physical batch plans."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w06-gate-02",
    "week_id": "week-06",
    "before": {
      "criterion": "Method-specific changes and extra supervision are disclosed; no unpublished shortcut is represented as replication.",
      "decided_at": null,
      "evidence": "",
      "id": "w06-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-06"
    },
    "values": {
      "criterion": "Selection scores use only complete clean epoch-20 development evaluations; pilots and corrupted scores cannot select configurations."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w06-gate-03",
    "week_id": "week-06",
    "before": {
      "criterion": "The 1,536-dimensional comparison is kept separate from the 512-dimensional table.",
      "decided_at": null,
      "evidence": "",
      "id": "w06-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-06"
    },
    "values": {
      "criterion": "Every attempt and failure is retained, and current allocation/memory/storage limits pass."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w07-gate-01",
    "week_id": "week-07",
    "before": {
      "criterion": "All 26 configurations pass implementation and licensed-provenance review; unresolved rows block complete replication.",
      "decided_at": null,
      "evidence": "",
      "id": "w07-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-07"
    },
    "values": {
      "criterion": "All 27 declared selection settings have an accounted attempt; every selected candidate has three valid seeds."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w07-gate-02",
    "week_id": "week-07",
    "before": {
      "criterion": "Shared settings, full selection budget and resource forecast are fixed before the main validation campaign.",
      "decided_at": null,
      "evidence": "",
      "id": "w07-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 3,
      "waiver_reason": "",
      "week_id": "week-07"
    },
    "values": {
      "criterion": "The three selected rates reproduce under the exact unrounded ranking rule and are immutably recorded before final training."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w07-gate-03",
    "week_id": "week-07",
    "before": {
      "criterion": "A documented schedule decision preserves the full declared scope rather than forcing a partial benchmark into the old deadline.",
      "decided_at": null,
      "evidence": "",
      "id": "w07-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-07"
    },
    "values": {
      "criterion": "Final training inputs, paired plans and allocation/capacity checks pass for all nine fresh heads."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w08-gate-01",
    "week_id": "week-08",
    "before": {
      "criterion": "Every planned selection trial or classified failure is accounted for.",
      "decided_at": null,
      "evidence": "",
      "id": "w08-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-08"
    },
    "values": {
      "criterion": "Every final attempt begins fresh and matches its selected rate, all-100-action inputs, paired seed and 20-epoch budget."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w08-gate-02",
    "week_id": "week-08",
    "before": {
      "criterion": "No novel-test loader or score was used for method, epoch or parameter selection.",
      "decided_at": null,
      "evidence": "",
      "id": "w08-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-08"
    },
    "values": {
      "criterion": "All completed heads have immutable epoch-20 checkpoints and valid health, pairing and provenance evidence."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w08-gate-03",
    "week_id": "week-08",
    "before": {
      "criterion": "Each method has a result-blind selected configuration under the same declared selection policy.",
      "decided_at": null,
      "evidence": "",
      "id": "w08-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-08"
    },
    "values": {
      "criterion": "Novel retrieval inputs and outcomes remain sealed while final training and any identical retries continue."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w09-gate-01",
    "week_id": "week-09",
    "before": {
      "criterion": "All scientific decisions and the 156-run roster are hash-bound and recorded before test opening.",
      "decided_at": null,
      "evidence": "",
      "id": "w09-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-09"
    },
    "values": {
      "criterion": "All nine final heads are complete and valid at epoch 20, with no selected checkpoint or configuration dependent on novel outcomes."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w09-gate-02",
    "week_id": "week-09",
    "before": {
      "criterion": "No unresolved implementation or selection blocker remains in the declared roster.",
      "decided_at": null,
      "evidence": "",
      "id": "w09-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-09"
    },
    "values": {
      "criterion": "The exact query/gallery identities and 180 unique evaluation cells are fixed and cross-bound to the complete final-run set."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w09-gate-03",
    "week_id": "week-09",
    "before": {
      "criterion": "The priority two-method phase alone cannot authorize novel evaluation.",
      "decided_at": null,
      "evidence": "",
      "id": "w09-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-09"
    },
    "values": {
      "criterion": "The independent audit and evaluation schedule preserves November 29 locks, December 6 results and December 7-18 delivery work."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w10-gate-01",
    "week_id": "week-10",
    "before": {
      "criterion": "All 156 final runs are present and verified, or the novel test remains sealed.",
      "decided_at": null,
      "evidence": "",
      "id": "w10-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-10"
    },
    "values": {
      "criterion": "The evaluator, role-specific caches, metrics and 180-cell verifier pass independent development/fixture checks."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w10-gate-02",
    "week_id": "week-10",
    "before": {
      "criterion": "Final retraining covers all 100 auxiliary actions and uses no novel-set checkpoint selection.",
      "decided_at": null,
      "evidence": "",
      "id": "w10-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-10"
    },
    "values": {
      "criterion": "Shared seal enforcement and authorization-before-loading checks pass across all scientific entrypoints."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w10-gate-03",
    "week_id": "week-10",
    "before": {
      "criterion": "Every final artifact matches the recorded selected setting and complete run-set lock.",
      "decided_at": null,
      "evidence": "",
      "id": "w10-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-10"
    },
    "values": {
      "criterion": "The final-run set and lock dependencies cross-bind all nine heads, exact identities and unchanged scientific settings."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w11-gate-01",
    "week_id": "week-11",
    "before": {
      "criterion": "The opening ledger proves all declared final training and selection preceded the first novel outcome.",
      "decided_at": null,
      "evidence": "",
      "id": "w11-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-11"
    },
    "values": {
      "criterion": "All nine final heads and the complete final lock are verified by November 29; no scientific training is active."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w11-gate-02",
    "week_id": "week-11",
    "before": {
      "criterion": "All 156 clean primary cells have authorized, finite, reproducible metrics and paired sample identities.",
      "decided_at": null,
      "evidence": "",
      "id": "w11-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-11"
    },
    "values": {
      "criterion": "Current historical-root, source, allocation and storage checks pass for the entire final evaluation campaign."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w11-gate-03",
    "week_id": "week-11",
    "before": {
      "criterion": "No missing method, selective rerun or changed statistical rule is concealed.",
      "decided_at": null,
      "evidence": "",
      "id": "w11-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 1,
      "waiver_reason": "",
      "week_id": "week-11"
    },
    "values": {
      "criterion": "The novel test remains unopened until the single authorized campaign; unresolved requirements are visible blockers."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w12-gate-01",
    "week_id": "week-12",
    "before": {
      "criterion": "All tables and intervals regenerate from authorized per-query results.",
      "decided_at": null,
      "evidence": "",
      "id": "w12-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-12"
    },
    "values": {
      "criterion": "The immutable dataset opening precedes all novel loading and binds the complete final authorization."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w12-gate-02",
    "week_id": "week-12",
    "before": {
      "criterion": "Claims respect the locked multiplicity rule and distinguish 512 versus 1,536 dimensions.",
      "decided_at": null,
      "evidence": "",
      "id": "w12-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-12"
    },
    "values": {
      "criterion": "All 180 required result cells are finite, unique, provenance-valid and reproducible from locked per-query evidence."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w12-gate-03",
    "week_id": "week-12",
    "before": {
      "criterion": "Every method, seed, failure, deviation and supplementary analysis is reported.",
      "decided_at": null,
      "evidence": "",
      "id": "w12-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 3,
      "waiver_reason": "",
      "week_id": "week-12"
    },
    "values": {
      "criterion": "No scientific training/selection occurs after opening; all operational attempts and any deviations remain visible."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w13-gate-01",
    "week_id": "week-13",
    "before": {
      "criterion": "The report distinguishes paper reproduction, motion adaptation and supplementary analyses.",
      "decided_at": null,
      "evidence": "",
      "id": "w13-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-13"
    },
    "values": {
      "criterion": "The conditional primary interval and all prespecified descriptive outputs regenerate from the locked records."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w13-gate-02",
    "week_id": "week-13",
    "before": {
      "criterion": "Every claim and comparison maps to a complete locked result.",
      "decided_at": null,
      "evidence": "",
      "id": "w13-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 3,
      "waiver_reason": "",
      "week_id": "week-13"
    },
    "values": {
      "criterion": "The confirmatory statement follows the upper-bound-below-zero rule; absolute accuracy and recipe-level/conditional limitations accompany it."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w13-gate-03",
    "week_id": "week-13",
    "before": {
      "criterion": "The public evidence package is license-safe and reproducible.",
      "decided_at": null,
      "evidence": "",
      "id": "w13-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-13"
    },
    "values": {
      "criterion": "The report includes all methods, seeds, cells, costs and failures without outcome-driven omissions or new superiority tests."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w14-gate-01",
    "week_id": "week-14",
    "before": {
      "criterion": "Completion requires the entire declared benchmark and its report, not merely reaching December 18.",
      "decided_at": null,
      "evidence": "",
      "id": "w14-gate-01",
      "position": 1,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-14"
    },
    "values": {
      "criterion": "The final report/poster and required outputs are delivered by December 18, or the incomplete study and dated amendment are explicitly recorded."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w14-gate-02",
    "week_id": "week-14",
    "before": {
      "criterion": "Unfinished work is visible with a dated continuation and preserved novel-test seal.",
      "decided_at": null,
      "evidence": "",
      "id": "w14-gate-02",
      "position": 2,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-14"
    },
    "values": {
      "criterion": "All nine final heads, 180 cells and declared analyses are independently evidenced before claiming empirical completion."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w14-gate-03",
    "week_id": "week-14",
    "before": {
      "criterion": "Source, permitted artifacts and tracker exports are independently recoverable.",
      "decided_at": null,
      "evidence": "",
      "id": "w14-gate-03",
      "position": 3,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-14"
    },
    "values": {
      "criterion": "Source, permitted evidence and reproduction instructions are recoverable and exclude licensed/private material."
    },
    "operation": "update"
  },
  {
    "table": "gates",
    "id": "w14-gate-04",
    "week_id": "week-14",
    "before": {
      "criterion": "Researcher time and retrospective are recorded without invented hours.",
      "decided_at": null,
      "evidence": "",
      "id": "w14-gate-04",
      "position": 4,
      "project_id": "pose-embed",
      "required": true,
      "state": "pending",
      "version": 2,
      "waiver_reason": "",
      "week_id": "week-14"
    },
    "values": {
      "criterion": "The live tracker/export matches v3 while preserving historical progress and actual hours without invented completions."
    },
    "operation": "update"
  },
  {
    "table": "sources",
    "id": "source-benchmark-v2",
    "week_id": null,
    "before": {
      "authors": "Pose Embed independent research",
      "canonical_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/configs/benchmark-methods.v2.json",
      "id": "source-benchmark-v2",
      "project_id": "pose-embed",
      "purpose": "All 26 required configurations, primary sources, implementation status and explicit adaptation blockers; see docs/protocol/protocol-v2.md.",
      "title": "Motion retrieval v2 method registry and protocol",
      "verified_at": "2026-09-24",
      "version": 1,
      "year": 2026
    },
    "values": {
      "purpose": "Historical 26-configuration v2 benchmark, preserved for provenance and future work. It is outside the December v3 study and does not authorize v3 execution."
    },
    "operation": "update"
  },
  {
    "table": "sources",
    "id": "source-plan-v3",
    "week_id": null,
    "before": null,
    "values": {
      "id": "source-plan-v3",
      "title": "Final v3 plan: frozen one-shot pose robustness",
      "authors": "Pose Embed independent research",
      "year": 2026,
      "canonical_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/plan/research-plan.v3.md",
      "purpose": "Final December execution design: three fixed recipes, 20 epochs, three seeds, nested corruption, conditional analysis and explicit capacity/test-opening gates; decision 0004 records the scope change.",
      "verified_at": "2026-09-29",
      "project_id": "pose-embed"
    },
    "operation": "insert"
  },
  {
    "table": "sources",
    "id": "source-supcon",
    "week_id": null,
    "before": null,
    "values": {
      "id": "source-supcon",
      "title": "Supervised Contrastive Learning",
      "authors": "Khosla et al.",
      "year": 2020,
      "canonical_url": "https://papers.nips.cc/paper_files/paper/2020/hash/d89a66c7c80a29b1bdbab0f2a1a94af8-Abstract.html",
      "purpose": "Published source for supervised contrastive learning; v3 declares the single-view temperature-0.07 pose adaptation as a descriptive comparator.",
      "verified_at": "2026-09-29",
      "project_id": "pose-embed"
    },
    "operation": "insert"
  },
  {
    "table": "week_sources",
    "id": "week-04:source-contextual",
    "week_id": "week-04",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Implement and validate the contextual objective and controlled comparators.",
      "source_id": "source-contextual",
      "version": 1,
      "week_id": "week-04"
    },
    "values": {
      "purpose": "Verify the fixed contextual recipe against published mathematics with independent forward/backward fixtures."
    },
    "operation": "update",
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-05:source-maskclr",
    "week_id": "week-05",
    "before": {
      "priority": "recommended",
      "project_id": "pose-embed",
      "purpose": "Supplementary corruption context only; implement the primary loss roster from the v2 registry.",
      "source_id": "source-maskclr",
      "version": 2,
      "week_id": "week-05"
    },
    "values": {
      "purpose": "Ground synthetic pose corruption choices while validating the exact nested v3 operators before selection."
    },
    "operation": "update",
    "source_id": "source-maskclr"
  },
  {
    "table": "week_sources",
    "id": "week-06:source-contextual",
    "week_id": "week-06",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Audit every architecture-specific comparison and its motion adaptation.",
      "source_id": "source-contextual",
      "version": 2,
      "week_id": "week-06"
    },
    "values": {
      "purpose": "Run the fixed three-recipe learning-rate matrix with paired clean development evidence."
    },
    "operation": "update",
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-07:source-contextual",
    "week_id": "week-07",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Verify all 26 declared configurations, licenses and resource feasibility before full selection.",
      "source_id": "source-contextual",
      "version": 2,
      "week_id": "week-07"
    },
    "values": {
      "purpose": "Apply the predeclared candidate eligibility and ranking rule without changing recipe parameters."
    },
    "operation": "update",
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-09:source-ntu",
    "week_id": "week-09",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Freeze multi-positive held-out identities while retaining the official one-shot task as supplementary.",
      "source_id": "source-ntu",
      "version": 2,
      "week_id": "week-09"
    },
    "values": {
      "purpose": "Verify official exemplars, action identities and the primary/exact-official query exclusions before locking evaluation."
    },
    "operation": "update",
    "source_id": "source-ntu"
  },
  {
    "table": "week_sources",
    "id": "week-10:source-prospectus",
    "week_id": "week-10",
    "before": {
      "priority": "recommended",
      "project_id": "pose-embed",
      "purpose": "Preserve the historical prospectus; v2 protocol and complete final roster supersede its narrow scope.",
      "source_id": "source-prospectus",
      "version": 2,
      "week_id": "week-10"
    },
    "values": {
      "purpose": "Audit the final v3 design while preserving the historical prospectus and prior protocols."
    },
    "operation": "update",
    "source_id": "source-prospectus"
  },
  {
    "table": "week_sources",
    "id": "week-11:source-contextual",
    "week_id": "week-11",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Evaluate every locked method; the v1 post-core Multi-Similarity exception does not apply.",
      "source_id": "source-contextual",
      "version": 2,
      "week_id": "week-11"
    },
    "values": {
      "purpose": "Complete all final locks and shared seal checks before novel evaluation; no post-core method additions."
    },
    "operation": "update",
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-12:source-motionbert",
    "week_id": "week-12",
    "before": {
      "priority": "recommended",
      "project_id": "pose-embed",
      "purpose": "Audit method and encoder reporting in the draft.",
      "source_id": "source-motionbert",
      "version": 1,
      "week_id": "week-12"
    },
    "values": {
      "purpose": "Verify the frozen encoder, cache provenance and all 180 final evaluation cells."
    },
    "operation": "update",
    "source_id": "source-motionbert"
  },
  {
    "table": "week_sources",
    "id": "week-13:source-bu-calendar",
    "week_id": "week-13",
    "before": {
      "priority": "recommended",
      "project_id": "pose-embed",
      "purpose": "Treat current semester dates as a planning horizon and record any necessary continuation.",
      "source_id": "source-bu-calendar",
      "version": 2,
      "week_id": "week-13"
    },
    "values": {
      "purpose": "Preserve the December 7-18 analysis/delivery window and reduced holiday/finals work budget."
    },
    "operation": "update",
    "source_id": "source-bu-calendar"
  },
  {
    "table": "week_sources",
    "id": "week-14:source-prospectus",
    "week_id": "week-14",
    "before": {
      "priority": "recommended",
      "project_id": "pose-embed",
      "purpose": "Archive the historical prospectus alongside the superseding v2 protocol.",
      "source_id": "source-prospectus",
      "version": 2,
      "week_id": "week-14"
    },
    "values": {
      "purpose": "Archive the final v3 plan beside the historical prospectus, prior protocols and recorded amendments."
    },
    "operation": "update",
    "source_id": "source-prospectus"
  },
  {
    "table": "week_sources",
    "id": "week-04:source-plan-v3",
    "week_id": "week-04",
    "before": null,
    "values": {
      "week_id": "week-04",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-05:source-plan-v3",
    "week_id": "week-05",
    "before": null,
    "values": {
      "week_id": "week-05",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-06:source-plan-v3",
    "week_id": "week-06",
    "before": null,
    "values": {
      "week_id": "week-06",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-07:source-plan-v3",
    "week_id": "week-07",
    "before": null,
    "values": {
      "week_id": "week-07",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-08:source-plan-v3",
    "week_id": "week-08",
    "before": null,
    "values": {
      "week_id": "week-08",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-09:source-plan-v3",
    "week_id": "week-09",
    "before": null,
    "values": {
      "week_id": "week-09",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-10:source-plan-v3",
    "week_id": "week-10",
    "before": null,
    "values": {
      "week_id": "week-10",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-11:source-plan-v3",
    "week_id": "week-11",
    "before": null,
    "values": {
      "week_id": "week-11",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-12:source-plan-v3",
    "week_id": "week-12",
    "before": null,
    "values": {
      "week_id": "week-12",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-13:source-plan-v3",
    "week_id": "week-13",
    "before": null,
    "values": {
      "week_id": "week-13",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-14:source-plan-v3",
    "week_id": "week-14",
    "before": null,
    "values": {
      "week_id": "week-14",
      "source_id": "source-plan-v3",
      "purpose": "Use the final v3 design, fixed schedule and stage-specific validity, capacity and novel-test gates for this week.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-plan-v3"
  },
  {
    "table": "week_sources",
    "id": "week-04:source-supcon",
    "week_id": "week-04",
    "before": null,
    "values": {
      "week_id": "week-04",
      "source_id": "source-supcon",
      "purpose": "Verify the declared single-view SupCon formulation and temperature adaptation.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "operation": "insert",
    "source_id": "source-supcon"
  },
  {
    "table": "week_sources",
    "id": "week-04:source-benchmark-v2",
    "week_id": "week-04",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-04"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-05:source-benchmark-v2",
    "week_id": "week-05",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-05"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-06:source-benchmark-v2",
    "week_id": "week-06",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-06"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-07:source-benchmark-v2",
    "week_id": "week-07",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-07"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-08:source-benchmark-v2",
    "week_id": "week-08",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-08"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-09:source-benchmark-v2",
    "week_id": "week-09",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-09"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-10:source-benchmark-v2",
    "week_id": "week-10",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-10"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-11:source-benchmark-v2",
    "week_id": "week-11",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-11"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-12:source-benchmark-v2",
    "week_id": "week-12",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-12"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-13:source-benchmark-v2",
    "week_id": "week-13",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-13"
    },
    "values": {},
    "operation": "delete"
  },
  {
    "table": "week_sources",
    "id": "week-14:source-benchmark-v2",
    "week_id": "week-14",
    "source_id": "source-benchmark-v2",
    "before": {
      "priority": "required",
      "project_id": "pose-embed",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "source_id": "source-benchmark-v2",
      "version": 1,
      "week_id": "week-14"
    },
    "values": {},
    "operation": "delete"
  }
]
$edits$::jsonb;
  edit jsonb;
  current_row jsonb;
  expected_row jsonb;
  assignments text;
  columns_sql text;
  changed_rows integer;
  expected_version integer;
  parent_id text;
begin
  if not exists (select 1 from public.projects where id = 'pose-embed') then
    raise notice 'pose-embed is not seeded; import research-plan.v3.json';
    return;
  end if;

  -- Lock each affected future week. A scope update never implicitly reopens it.
  for parent_id in
    select distinct value->>'week_id' from jsonb_array_elements(edits)
    where value->>'week_id' is not null order by 1
  loop
    if parent_id < 'week-04' then raise exception 'Historical week change forbidden'; end if;
    select to_jsonb(w) into current_row from public.weeks w
      where id = parent_id and project_id = 'pose-embed' for update;
    if current_row is null or current_row->>'state' = 'closed'
       or current_row->>'closed_at' is not null then
      raise exception using errcode = '40001',
        message = parent_id || ' is missing or closed; an audited reopen is required';
    end if;
  end loop;

  for edit in select value from jsonb_array_elements(edits)
  loop
    if edit->>'table' not in ('projects', 'weeks', 'tasks', 'gates', 'sources', 'week_sources') then
      raise exception 'Unexpected migration table';
    end if;
    if edit->>'table' = 'week_sources' then
      select to_jsonb(t) into current_row from public.week_sources t
        where project_id = 'pose-embed' and week_id = edit->>'week_id'
          and source_id = edit->>'source_id' for update;
    elsif edit->>'table' = 'projects' then
      select to_jsonb(t) into current_row from public.projects t
        where id = 'pose-embed' and id = edit->>'id' for update;
    else
      execute format('select to_jsonb(t) from public.%I t where id = $1 and project_id = ''pose-embed'' for update', edit->>'table')
        into current_row using edit->>'id';
    end if;

    if edit->>'operation' = 'insert' then
      expected_row := edit->'values' || jsonb_build_object('version', 1);
      if current_row is not null then
        if current_row @> expected_row then continue; end if;
        raise exception using errcode = '40001', message = edit->>'id' || ' already exists with different content';
      end if;
      select string_agg(format('%I', key), ', ' order by key),
             string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, assignments from jsonb_object_keys(expected_row) key;
      execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
        edit->>'table', columns_sql, assignments, edit->>'table') using expected_row;
      continue;
    end if;

    expected_version := (edit->'before'->>'version')::integer;
    if edit->>'operation' = 'delete' then
      if edit->>'table' <> 'week_sources' then raise exception 'Unexpected deletion'; end if;
      if current_row is null then continue; end if;
    else
      expected_row := edit->'before' || edit->'values' || jsonb_build_object('version', expected_version + 1);
      if current_row @> expected_row then continue; end if;
    end if;
    if current_row is null or not (current_row @> (edit->'before')) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed; refusing to overwrite live progress';
    end if;
    if edit->>'operation' = 'delete' then
      delete from public.week_sources where project_id = 'pose-embed'
        and week_id = edit->>'week_id' and source_id = edit->>'source_id'
        and version = expected_version;
    else
      select string_agg(format('%I = v.%I', key, key), ', ' order by key)
        into assignments from jsonb_object_keys(edit->'values') key;
      if edit->>'table' = 'week_sources' then
        execute format('update public.week_sources t set %s from jsonb_populate_record(null::public.week_sources, $1) v where t.project_id = ''pose-embed'' and t.week_id = $2 and t.source_id = $3 and t.version = $4 returning to_jsonb(t)', assignments)
          into current_row using edit->'values', edit->>'week_id', edit->>'source_id', expected_version;
      else
        execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.version = $3 returning to_jsonb(t)',
          edit->>'table', assignments, edit->>'table') into current_row
          using edit->'values', edit->>'id', expected_version;
      end if;
    end if;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001', message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
