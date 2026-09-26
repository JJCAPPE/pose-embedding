-- Researcher-directed v2 scope; expected versions from the public live snapshot
-- 2026-09-24T22:35:10Z, including the confirmed BU determination.
-- Preserve prior completions, actual time, ownership and all audit history.
-- Fresh databases use the v2 importer; never reseed an existing project.
do $migration$
declare
  edits constant jsonb := $edits$
[
  {
    "table": "projects",
    "id": "pose-embed",
    "week_id": null,
    "before": {
      "id": "pose-embed",
      "slug": "pose-embed",
      "title": "Robust human-motion retrieval",
      "research_question": "Given one clean reference per unseen action, does contextual training reduce retrieval degradation when query joints or frames are inaccurate or missing?",
      "summary": "A leakage-free, reproducible comparison of metric-learning objectives for one-shot action retrieval from corrupted pose sequences.",
      "start_date": "2026-09-15",
      "end_date": "2026-12-18",
      "timezone": "America/New_York",
      "visibility": "public",
      "version": 2
    },
    "values": {
      "title": "Metric learning for human-motion retrieval",
      "research_question": "Does contextual similarity learning improve motion retrieval relative to the full image-paper comparison roster, including Multi-Similarity with and without mining?",
      "summary": "A controlled motion-domain replication: contextual versus contrastive development first, followed by all 26 declared configurations with a common fine-tuned MotionBERT backbone. The current dates are a provisional planning horizon, subject to measured resources and complete method coverage."
    }
  },
  {
    "table": "weeks",
    "id": "week-01",
    "week_id": "week-01",
    "before": {
      "id": "week-01",
      "project_id": "pose-embed",
      "number": 1,
      "start_date": "2026-09-15",
      "end_date": "2026-09-20",
      "phase": "Protocol",
      "title": "Protocol and access",
      "objective": "Turn the prospectus into a documented, hash-bound, testable protocol and prove that the required data and compute are reachable.",
      "deliverable": "A documented, hash-bound protocol-v1, verified data and checkpoint inventory, and measured GPU profile.",
      "risks": [
        "NTU or checkpoint access may require manual license acceptance.",
        "GPU availability may not match the planned memory or runtime assumptions.",
        "Protocol amendments or the BU determination may remain unresolved after technical setup begins."
      ],
      "advisor_prompt": "Are the research question, test-opening rule, primary estimand, synchronized-view exclusion, and claim language documented as the binding protocol?",
      "reflection": "Week 1 established a documented, hash-bound protocol, verified the licensed HRNet aggregate, official one-shot split, and MotionBERT checkpoint, and confirmed physical batch 32 on an SCC A40. The GPU-host inventory accounts for 113,945 usable annotations plus 535 official missing-skeleton exclusions. The researcher adopted the result-blind aggregate-aware input contract on 2026-09-24 and confirmed that BU has issued the applicable governance determination. No determination attachment is required. Researcher-supplied actual minutes and final weekly closeout remain pending; the novel test remains sealed and the weekly record remains open.",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "blocked",
      "closed_at": null,
      "version": 6
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w01-task-01",
    "week_id": "week-01",
    "before": {
      "id": "w01-task-01",
      "week_id": "week-01",
      "position": 1,
      "title": "Finalize protocol-v1",
      "details": "Resolve the objective formula, primary estimand, claim rule, validation split, synchronized-view rule, corruptions, test-opening rule, and failed-run policy.",
      "expected_output": "Documented, hash-bound protocol document.",
      "required": true,
      "estimate_minutes": 120,
      "state": "done",
      "completion_note": "All binding scientific choices were confirmed, including mandatory final training on all 100 auxiliary actions. Independent research governance is recorded in docs/protocol/independent-research.md. The result-blind NTU input-contract amendment was adopted on 2026-09-24. Current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/independent-research.md",
      "completed_at": "2026-09-11T17:41:08+00:00",
      "version": 5,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w01-task-02",
    "week_id": "week-01",
    "before": {
      "id": "w01-task-02",
      "week_id": "week-01",
      "position": 2,
      "title": "Verify licensed inputs",
      "details": "Confirm that the NTU HRNet-derived poses, official one-shot split, and pretrained MotionBERT checkpoint are readable. Record source URLs and SHA-256 checksums without committing licensed files.",
      "expected_output": "Input inventory and checksum report.",
      "required": true,
      "estimate_minutes": 120,
      "state": "done",
      "completion_note": "Verified 2026-09-24: dataset access remains active, the complete usable HRNet aggregate, official missing-skeleton list, one-shot definition, and MotionBERT checkpoint are readable and checksummed on the GPU host. The aggregate contains 113,945 usable annotations and all 20 official exemplars; the official 535-item missing-skeleton list accounts for the remaining nominal captures. The result-blind aggregate-aware input contract is adopted in docs/protocol/input-contract-amendment.v1.md, and w01-gate-02 is met. The novel test remains sealed.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md",
      "completed_at": "2026-09-24T15:35:26+00:00",
      "version": 7,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w01-task-03",
    "week_id": "week-01",
    "before": {
      "id": "w01-task-03",
      "week_id": "week-01",
      "position": 3,
      "title": "Profile the GPU path",
      "details": "Run one representative frozen MotionBERT forward pass at batch sizes 32 and 64. Record device, CUDA, memory, runtime, scheduler, quota, and job limits.",
      "expected_output": "Compute profile with a justified physical batch-size decision.",
      "required": true,
      "estimate_minutes": 120,
      "state": "done",
      "completion_note": "Completed 2026-09-16: a real frozen MotionBERT encoder profile ran on a scheduler-assigned BU SCC A40 using dense protocol-shaped float32 inputs. Physical batch 32 completed with 2.572 GiB peak allocated, 2.855 GiB peak reserved, and an 842.164 ms median forward; batch 64 completed with 4.977 GiB allocated, 5.514 GiB reserved, and a 1,685.400 ms median. Required device, CUDA, scheduler, quota, and job-limit evidence was captured. Physical batch 32 remains selected because protocol v1 permits 64 only after all core methods fit. This is compute evidence only, not preprocessing or encoder-parity evidence.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-gpu-profile.md",
      "completed_at": "2026-09-16T16:41:15+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w01-task-04",
    "week_id": "week-01",
    "before": {
      "id": "w01-task-04",
      "week_id": "week-01",
      "position": 4,
      "title": "Record governance decisions",
      "details": "Record researcher-controlled protocol decisions and the BU data-governance or human-subjects determination. Record unresolved conditions verbatim.",
      "expected_output": "Decision evidence or a visible blocking record.",
      "required": true,
      "estimate_minutes": 60,
      "state": "done",
      "completion_note": "The computational scope is recorded in docs/compliance/computational-research-scope.md. On 2026-09-24, the researcher confirmed that BU has issued the applicable human-subjects/data-governance determination and requested completion without attaching proof. The confirmation is recorded and w01-gate-04 is met. This is researcher confirmation, not independent document verification; no specific institutional classification or original decision date is asserted.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md",
      "completed_at": "2026-09-16T16:07:48+00:00",
      "version": 5,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w01-task-05",
    "week_id": "week-01",
    "before": {
      "id": "w01-task-05",
      "week_id": "week-01",
      "position": 5,
      "title": "Close the weekly record",
      "details": "Update actual hours, blockers, evidence links, and the first-week reflection in the tracker.",
      "expected_output": "A complete Week 1 progress record.",
      "required": true,
      "estimate_minutes": 60,
      "state": "blocked",
      "completion_note": "Verified inputs, remote setup, the adopted result-blind input contract, and the researcher-confirmed BU determination are recorded. Final closeout remains blocked until researcher-supplied actual minutes are recorded. No hours or week closure are inferred.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md",
      "completed_at": null,
      "version": 6,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "gates",
    "id": "w01-gate-01",
    "week_id": "week-01",
    "before": {
      "id": "w01-gate-01",
      "week_id": "week-01",
      "position": 1,
      "criterion": "Protocol-v1 is documented under researcher control and its hash is recorded.",
      "required": true,
      "state": "met",
      "evidence": "Independent research governance is recorded in docs/protocol/independent-research.md. The result-blind NTU input-contract amendment is recorded in docs/protocol/input-contract-amendment.v1.md. Current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f.",
      "waiver_reason": "",
      "decided_at": "2026-09-11T17:41:08+00:00",
      "version": 4,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "gates",
    "id": "w01-gate-02",
    "week_id": "week-01",
    "before": {
      "id": "w01-gate-02",
      "week_id": "week-01",
      "position": 2,
      "criterion": "Verified input inventory matches the recorded protocol input contract.",
      "required": true,
      "state": "met",
      "evidence": "Verified 2026-09-24: the local and GPU-host inputs account for 113,945 usable HRNet annotations plus 535 official missing-skeleton exclusions, totaling 114,480 nominal captures. The hash-pinned aggregate and official missing-skeleton list passed aggregate-aware physical-source verification. The researcher adopted the result-blind contract in https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/input-contract-amendment.v1.md; current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f. GPU-host evidence: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-remote-setup.md. The novel test remains sealed.",
      "waiver_reason": "",
      "decided_at": "2026-09-24T16:25:10+00:00",
      "version": 6,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "gates",
    "id": "w01-gate-03",
    "week_id": "week-01",
    "before": {
      "id": "w01-gate-03",
      "week_id": "week-01",
      "position": 3,
      "criterion": "A representative GPU profile confirms a feasible physical batch size.",
      "required": true,
      "state": "met",
      "evidence": "Verified 2026-09-16: frozen MotionBERT completed the protocol-shaped physical batch 32 profile on a scheduler-assigned BU SCC A40, and all required device, CUDA, memory, runtime, scheduler, quota, and job-limit evidence was captured. Physical batch 32 is feasible and remains selected pending the Week 4 all-core-method batch-64 profile. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/week-1-gpu-profile.md.",
      "waiver_reason": "",
      "decided_at": "2026-09-16T16:41:15+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "gates",
    "id": "w01-gate-04",
    "week_id": "week-01",
    "before": {
      "id": "w01-gate-04",
      "week_id": "week-01",
      "position": 4,
      "criterion": "Required BU governance determination is recorded.",
      "required": true,
      "state": "met",
      "evidence": "Recorded 2026-09-24 on researcher confirmation: BU has issued the applicable human-subjects/data-governance determination. The researcher requested completion without attaching proof; no document attachment is required. This records the confirmation, not independent document verification or the institution's original decision date. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/compliance/computational-research-scope.md.",
      "waiver_reason": "",
      "decided_at": "2026-09-24T22:13:07+00:00",
      "version": 3,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "weeks",
    "id": "week-02",
    "week_id": "week-02",
    "before": {
      "id": "week-02",
      "project_id": "pose-embed",
      "number": 2,
      "start_date": "2026-09-21",
      "end_date": "2026-09-27",
      "phase": "Data",
      "title": "Immutable data manifests",
      "objective": "Create deterministic sample identities and split manifests that make class, exemplar, and synchronized-view leakage impossible.",
      "deliverable": "Checksummed manifests for development, final training, anchors, and both novel-query definitions, plus a leakage audit.",
      "risks": [
        "NTU filename parsing mistakes can silently merge performances.",
        "Synchronized cameras can leak the anchor performance into queries.",
        "Upstream one-shot files may use a different action index convention."
      ],
      "advisor_prompt": "Does the primary deduplicated query definition answer the intended question while the exact-official query set preserves comparability?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w02-task-01",
    "week_id": "week-02",
    "before": {
      "id": "w02-task-01",
      "week_id": "week-02",
      "position": 1,
      "title": "Parse NTU sample identities",
      "details": "Parse setup, camera, performer, replication, action, and body metadata from canonical filenames. Reject malformed and duplicate identifiers.",
      "expected_output": "Tested parser and normalized sample inventory.",
      "required": true,
      "estimate_minutes": 120,
      "state": "done",
      "completion_note": "Implemented a hash-before-deserialization NTU HRNet importer and canonical S/C/P/R/A parser. Normalized 113,945 unique usable samples with frame count, tensor shapes, pose-track count, and nonempty-track count; malformed identifiers, duplicate aliases, label disagreement, invalid body metadata, missing-listed overlap, and non-finite arrays are rejected.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md",
      "completed_at": "2026-09-16T01:58:25+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w02-task-02",
    "week_id": "week-02",
    "before": {
      "id": "w02-task-02",
      "week_id": "week-02",
      "position": 2,
      "title": "Generate split manifests",
      "details": "Generate the 80-class development train, 20-class class-disjoint validation, final 100-class train, official novel, anchor, deduplicated-primary query, and exact-official query manifests.",
      "expected_output": "Seven deterministic, checksummed manifest files.",
      "required": true,
      "estimate_minutes": 180,
      "state": "done",
      "completion_note": "Generated seven immutable JSONL manifests from the locked class and exemplar policy: 76,013 development-train, 18,988 development-validation, 95,001 final-train, 18,944 official-novel, 20 anchor, 18,884 primary-query, and 18,924 exact-official-query records. The audit records every SHA-256 digest and generation input.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md",
      "completed_at": "2026-09-16T01:58:25+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w02-task-03",
    "week_id": "week-02",
    "before": {
      "id": "w02-task-03",
      "week_id": "week-02",
      "position": 3,
      "title": "Prove leakage invariants",
      "details": "Test class disjointness, anchor uniqueness, sample uniqueness, synchronized-performance exclusions, stable ordering, and complete file coverage.",
      "expected_output": "Passing leakage and duplication test suite.",
      "required": true,
      "estimate_minutes": 120,
      "state": "done",
      "completion_note": "Automated checks prove class disjointness, one anchor per novel class, source and manifest identity uniqueness, exact exclusion of 40 synchronized camera mates, stable ordering, and complete 113,945-sample source coverage. An independent regeneration was byte-identical to the published release bundle.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md",
      "completed_at": "2026-09-16T01:58:25+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "tasks",
    "id": "w02-task-04",
    "week_id": "week-02",
    "before": {
      "id": "w02-task-04",
      "week_id": "week-02",
      "position": 4,
      "title": "Publish the manifest audit",
      "details": "Record counts by class and split, checksum every manifest, and explain every query excluded from the primary set.",
      "expected_output": "Human-readable manifest audit report.",
      "required": true,
      "estimate_minutes": 60,
      "state": "done",
      "completion_note": "Published a source-safe manifest audit with per-class counts, all manifest digests, body-metadata coverage, invariant results, and one explicit explanation for each of the 40 synchronized-view exclusions. The required result-blind amendment is explicitly scoped to both the 114,480-versus-113,945 count and aggregate-aware source verification.",
      "evidence_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md",
      "completed_at": "2026-09-16T01:58:25+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "gates",
    "id": "w02-gate-01",
    "week_id": "week-02",
    "before": {
      "id": "w02-gate-01",
      "week_id": "week-02",
      "position": 1,
      "criterion": "All seven manifests have frozen counts and checksums.",
      "required": true,
      "state": "met",
      "evidence": "Seven immutable release manifests have frozen counts and SHA-256 checksums for the verified 113,945-sample usable aggregate; the 535 official missing-skeleton exclusions account for all 114,480 nominal captures. Aggregate-aware physical-source verification and independent byte-identical regeneration passed. The researcher adopted the result-blind contract in https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/input-contract-amendment.v1.md; current protocol SHA-256: c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f. Manifest audit: https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v2.md.",
      "waiver_reason": "",
      "decided_at": "2026-09-24T16:25:10+00:00",
      "version": 4,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "gates",
    "id": "w02-gate-02",
    "week_id": "week-02",
    "before": {
      "id": "w02-gate-02",
      "week_id": "week-02",
      "position": 2,
      "criterion": "Automated checks find zero forbidden overlap or duplicate identities.",
      "required": true,
      "state": "met",
      "evidence": "Verified 2026-09-15: automated construction-time and unit-test invariants found zero forbidden class, anchor/query, synchronized-performance, source-identity, or manifest-identity overlap; complete source coverage and byte-stable regeneration also passed. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md.",
      "waiver_reason": "",
      "decided_at": "2026-09-16T01:58:25+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "gates",
    "id": "w02-gate-03",
    "week_id": "week-02",
    "before": {
      "id": "w02-gate-03",
      "week_id": "week-02",
      "position": 3,
      "criterion": "Every synchronized-view exclusion is reproducible from the manifest audit.",
      "required": true,
      "state": "met",
      "evidence": "Verified 2026-09-15: the audit enumerates all 40 primary-query exclusions and derives each one as a synchronized camera mate sharing the anchor setup, performer, repetition, and action. See https://github.com/JJCAPPE/pose-embedding/blob/main/docs/protocol/ntu-manifest-audit.v1.md.",
      "waiver_reason": "",
      "decided_at": "2026-09-16T01:58:25+00:00",
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "weeks",
    "id": "week-03",
    "week_id": "week-03",
    "before": {
      "id": "week-03",
      "project_id": "pose-embed",
      "number": 3,
      "start_date": "2026-09-28",
      "end_date": "2026-10-04",
      "phase": "Representation",
      "title": "Frozen encoder and evaluator",
      "objective": "Build a deterministic frozen MotionBERT feature path and a trustworthy one-shot retrieval evaluator.",
      "deliverable": "Repeatable clean feature caches, verified retrieval metrics, and measured extraction cost.",
      "risks": [
        "The legacy upstream code assumes CUDA DataParallel and outdated dependencies.",
        "Pooling or normalization drift can invalidate comparison with MotionBERT.",
        "Feature caching without provenance can mix incompatible experiments."
      ],
      "advisor_prompt": "Are the frozen encoder, 2,048-dimensional head interface, cosine retrieval, and reported metrics faithful to the prospectus?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "reflection": "Implemented the clean frozen encoder, parity checks, immutable caches, fixed development episode and retrieval tests ahead of Week 3. Synthetic checks are not real GPU evidence. The institutional determination is still pending, so no scientific extraction was launched and the novel test remains sealed. Actual research minutes and the researcher checkpoint response have not been supplied. See docs/protocol/week-3-implementation.md. This records v1 frozen-pilot software evidence only. V2 multi-positive metrics, fine-tuning and broad method parity remain uncompleted. Week state stays planned until prior weekly records close."
    }
  },
  {
    "table": "tasks",
    "id": "w03-task-01",
    "week_id": "week-03",
    "before": {
      "id": "w03-task-01",
      "week_id": "week-03",
      "position": 1,
      "title": "Port minimal MotionBERT inference",
      "details": "Adapt only the required encoder modules with upstream notices. Load the pinned checkpoint, set evaluation mode, and prove every encoder parameter is frozen.",
      "expected_output": "Device-agnostic frozen encoder with attribution.",
      "required": true,
      "estimate_minutes": 150,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "Implemented the shared strict checkpoint loader, frozen/eval encoder and attributed preprocessing adapter. Synthetic tests against the pinned upstream pass. The fixed 48-sample real auxiliary parity run remains pending; no GPU parity claim is made. See docs/protocol/week-3-implementation.md."
    }
  },
  {
    "table": "tasks",
    "id": "w03-task-02",
    "week_id": "week-03",
    "before": {
      "id": "w03-task-02",
      "week_id": "week-03",
      "position": 2,
      "title": "Build provenance-aware feature caching",
      "details": "Cache features by data, manifest, model, checkpoint, preprocessing, corruption, and code hashes. Reject partial or mismatched caches.",
      "expected_output": "Repeatable cache plus machine-readable provenance manifest.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "in_progress",
      "completion_note": "Implemented clean float32 8,704-value deterministic caches, complete source/code/parity/checkpoint binding, immutable publication and fail-closed validation. Synthetic extraction and tamper tests pass; real cache provenance still awaits the scientific GPU run. See docs/protocol/week-3-implementation.md."
    }
  },
  {
    "table": "tasks",
    "id": "w03-task-03",
    "week_id": "week-03",
    "before": {
      "id": "w03-task-03",
      "week_id": "week-03",
      "position": 3,
      "title": "Implement retrieval evaluation",
      "details": "Implement cosine ranking, top-1, MRR, and R@5. Verify ties and missing-relevant-item errors using hand-calculated fixtures.",
      "expected_output": "Metric module with exact fixture tests.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "done",
      "completion_note": "Verified 2026-09-24: ranks [1, 2, 6] produce top-1 1/3, MRR 5/9 and R@5 2/3. Tests cover stable exact ties, zero/nonfinite vectors, duplicate query IDs, missing relevant items and synchronized-view leakage. Fixed result-blind development episode generation is implemented. See docs/protocol/week-3-implementation.md.",
      "completed_at": "2026-09-24T21:50:28+00:00"
    }
  },
  {
    "table": "tasks",
    "id": "w03-task-04",
    "week_id": "week-03",
    "before": {
      "id": "w03-task-04",
      "week_id": "week-03",
      "position": 4,
      "title": "Measure extraction reproducibility",
      "details": "Run clean extraction twice, compare outputs, and record full-dataset runtime and storage projections.",
      "expected_output": "Determinism report and remaining-compute forecast.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "blocked",
      "completion_note": "The scheduler runner and full-cache repeatability/resource verifier are implemented. No scientific GPU extraction was launched because the existing BU institutional determination remains unresolved. Two fresh 95,001-row runs and their measured resource evidence are still required. See docs/protocol/week-3-implementation.md."
    }
  },
  {
    "table": "tasks",
    "id": "w03-task-05",
    "week_id": "week-03",
    "before": null,
    "values": {
      "id": "w03-task-05",
      "week_id": "week-03",
      "position": 5,
      "title": "Validate v2 retrieval and protocol transition",
      "details": "Keep v1 fixture evidence. Independently test multi-positive relevance, self/synchronized-view exclusions, R@K, AP, mAP@R and dimension groups; verify the v2 gate prevents novel opening before all methods are complete.",
      "expected_output": "New v2 correctness fixtures and sealed-test validation; no reuse of v1 completion as v2 completion.",
      "required": true,
      "estimate_minutes": 180,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "project_id": "pose-embed"
    }
  },
  {
    "table": "gates",
    "id": "w03-gate-01",
    "week_id": "week-03",
    "before": {
      "id": "w03-gate-01",
      "week_id": "week-03",
      "position": 1,
      "criterion": "Two clean feature extractions are identical within the declared tolerance.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "evidence": "Byte-identical synthetic caches and the full 95,001-row verification command are tested. Two real extractions on the same GPU are still required; no scientific repeatability result exists yet."
    }
  },
  {
    "table": "gates",
    "id": "w03-gate-02",
    "week_id": "week-03",
    "before": {
      "id": "w03-gate-02",
      "week_id": "week-03",
      "position": 2,
      "criterion": "Hand-calculated top-1, MRR, and R@5 fixtures pass.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "state": "met",
      "evidence": "Verified 2026-09-24: tests/unit/test_evaluation.py checks ranks [1, 2, 6], top-1=1/3, MRR=5/9 and R@5=2/3, plus ties and invalid inputs. See docs/protocol/week-3-implementation.md.",
      "decided_at": "2026-09-24T21:50:28+00:00"
    }
  },
  {
    "table": "gates",
    "id": "w03-gate-03",
    "week_id": "week-03",
    "before": {
      "id": "w03-gate-03",
      "week_id": "week-03",
      "position": 3,
      "criterion": "Every cache contains complete provenance and incompatible reuse fails closed.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "evidence": "Complete binding, immutable publication and tamper-rejection tests pass on synthetic inputs. The real final/development caches must still be produced and individually verified before this gate is met."
    }
  },
  {
    "table": "gates",
    "id": "w03-gate-04",
    "week_id": "week-03",
    "before": {
      "id": "w03-gate-04",
      "week_id": "week-03",
      "position": 4,
      "criterion": "Measured extraction time and storage fit the remaining schedule.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "evidence": "The conservative slower-run forecast and all limit checks are implemented and unit-tested. Actual full-run time, memory and storage have not yet been measured; the old encoder-only profile is not a substitute."
    }
  },
  {
    "table": "gates",
    "id": "w03-gate-05",
    "week_id": "week-03",
    "before": null,
    "values": {
      "id": "w03-gate-05",
      "week_id": "week-03",
      "position": 5,
      "criterion": "V2 multi-positive retrieval and full-roster test-seal checks pass independently of the historical one-shot metric gate.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "project_id": "pose-embed"
    }
  },
  {
    "table": "weeks",
    "id": "week-04",
    "week_id": "week-04",
    "before": {
      "id": "week-04",
      "project_id": "pose-embed",
      "number": 4,
      "start_date": "2026-10-05",
      "end_date": "2026-10-11",
      "phase": "Objectives",
      "title": "Heads, losses, and sampler",
      "objective": "Implement the identical embedding head and three core objectives under one paired, balanced training pipeline.",
      "deliverable": "Verified core objectives, balanced batch sampler, and an end-to-end tiny-set overfit run.",
      "risks": [
        "Contextual loss is invalid when batches are not class-balanced.",
        "Different initializations or batch order would weaken paired comparisons.",
        "A numerically finite loss can still collapse embeddings."
      ],
      "advisor_prompt": "Do the shared head, physical P by K batches, and equal implementation path isolate the objective as the intended independent variable?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Priority pair on development",
      "objective": "Run Contextual and its contrastive component first on the same clean development problem, with the common fine-tuned backbone.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-01",
    "week_id": "week-04",
    "before": {
      "id": "w04-task-01",
      "week_id": "week-04",
      "position": 1,
      "title": "Implement the shared embedding head",
      "details": "Reproduce mean pooling over time and people, a linear 17 by 512 to 2,048 projection, and L2 normalization for every objective.",
      "expected_output": "One tested head implementation shared by all methods.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Adopt the v2 amendment and method registry",
      "details": "Record source-paper mapping, all 26 configurations, common settings and explicit unresolved blockers.",
      "expected_output": "Record source-paper mapping, all 26 configurations, common settings and explicit unresolved blockers."
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-02",
    "week_id": "week-04",
    "before": {
      "id": "w04-task-02",
      "week_id": "week-04",
      "position": 2,
      "title": "Implement three core objectives",
      "details": "Implement contrastive-only, supervised contrastive, and contextual-plus-contrastive using the audited contextual defaults and exact objective weighting.",
      "expected_output": "Finite-value and finite-gradient tests for all core losses.",
      "required": true,
      "estimate_minutes": 180,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Implement the priority two-method path",
      "details": "Use independent paper-faithful Contextual and exact contrastive component, finite gradient/reference tests, and common fine-tuned MotionBERT.",
      "expected_output": "Use independent paper-faithful Contextual and exact contrastive component, finite gradient/reference tests, and common fine-tuned MotionBERT."
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-03",
    "week_id": "week-04",
    "before": {
      "id": "w04-task-03",
      "week_id": "week-04",
      "position": 3,
      "title": "Pair batches across objectives",
      "details": "Create deterministic P=8, K=4 physical batches with the same samples and order for each method. Profile batch 64 without changing the default unless every method fits.",
      "expected_output": "Persisted batch manifest and balance assertions.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Run paired development smoke and overfit checks",
      "details": "Run both methods from identical initialization and batch plan; retain every attempt and six-seed pairing design without touching novel data.",
      "expected_output": "Run both methods from identical initialization and batch plan; retain every attempt and six-seed pairing design without touching novel data."
    }
  },
  {
    "table": "tasks",
    "id": "w04-task-04",
    "week_id": "week-04",
    "before": {
      "id": "w04-task-04",
      "week_id": "week-04",
      "position": 4,
      "title": "Run golden and overfit checks",
      "details": "Compare contextual forward values and gradients with the audited reference, then make each objective lower loss and overfit the tiny fixture.",
      "expected_output": "Golden-equivalence report and three successful debug runs.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Measure feasibility before broadening",
      "details": "Measure real forward/backward time, memory and storage; forecast 156 final runs plus selection trials and revise provisional dates.",
      "expected_output": "Measure real forward/backward time, memory and storage; forecast 156 final runs plus selection trials and revise provisional dates."
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-01",
    "week_id": "week-04",
    "before": {
      "id": "w04-gate-01",
      "week_id": "week-04",
      "position": 1,
      "criterion": "All objectives lower loss and overfit the same debug set.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Both priority methods pass independent value/gradient and common-debug-set checks."
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-02",
    "week_id": "week-04",
    "before": {
      "id": "w04-gate-02",
      "week_id": "week-04",
      "position": 2,
      "criterion": "Contextual outputs and gradients match the golden reference.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "No novel-test data or score was loaded; paired initialization, batches and development provenance are complete."
    }
  },
  {
    "table": "gates",
    "id": "w04-gate-03",
    "week_id": "week-04",
    "before": {
      "id": "w04-gate-03",
      "week_id": "week-04",
      "position": 3,
      "criterion": "Balanced batches, paired sample order, and identical head initialization are verified.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "The measured resource forecast and researcher workload decision determine the next schedule; v1 frozen-forward memory is not reused as fine-tuning evidence."
    }
  },
  {
    "table": "weeks",
    "id": "week-05",
    "week_id": "week-05",
    "before": {
      "id": "week-05",
      "project_id": "pose-embed",
      "number": 5,
      "start_date": "2026-10-12",
      "end_date": "2026-10-18",
      "phase": "Robustness",
      "title": "Corruption freeze",
      "objective": "Implement and visually validate deterministic query-only corruptions before any validation comparison can influence their design.",
      "deliverable": "A frozen corruptions-v1 specification, visual audit, and deterministic test suite.",
      "risks": [
        "Fixed coordinate noise may not be comparable across body scales.",
        "Masking can accidentally alter the gallery or tensor length.",
        "Severity levels can be imperceptible or geometrically degenerate."
      ],
      "advisor_prompt": "Do the three corruption families and levels represent plausible input failures without changing the action label or testing a different task?",
      "reflection": "",
      "planned_minutes": 300,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Published loss baselines",
      "objective": "Implement the paper loss-comparison families under the shared encoder, head, sampler and development-selection budget.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-01",
    "week_id": "week-05",
    "before": {
      "id": "w05-task-01",
      "week_id": "week-05",
      "position": 1,
      "title": "Implement scale-normalized jitter",
      "details": "Apply deterministic Gaussian xy noise at 1%, 2.5%, and 5% of each clean sequence's median torso scale.",
      "expected_output": "Jitter operator with deterministic hashes and geometry tests.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Implement pair and triplet losses",
      "details": "Implement Triplet, MS, MS + miner and NT-Xent with exact distance, normalization and mining semantics.",
      "expected_output": "Implement Triplet, MS, MS + miner and NT-Xent with exact distance, normalization and mining semantics."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-02",
    "week_id": "week-05",
    "before": {
      "id": "w05-task-02",
      "week_id": "week-05",
      "position": 2,
      "title": "Implement joint and frame masking",
      "details": "Mask 3, 6, or 8 connected limb-first joint trajectories, or a consecutive 10, 25, or 40-frame block. Set coordinates and confidence to zero without resampling.",
      "expected_output": "Joint and frame operators with exact affected-count tests.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Implement proxy and classification losses",
      "details": "Implement Proxy Anchor, Proxy NCA, Proxy NCA++ and normalized softmax with documented proxy learning rates and initialization.",
      "expected_output": "Implement Proxy Anchor, Proxy NCA, Proxy NCA++ and normalized softmax with documented proxy learning rates and initialization."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-03",
    "week_id": "week-05",
    "before": {
      "id": "w05-task-03",
      "week_id": "week-05",
      "position": 3,
      "title": "Inspect representative corruptions",
      "details": "Render fixed examples for every family and level. Check visibility, action-label preservation, temporal placement, and monotonic geometric severity.",
      "expected_output": "Reviewable corruption contact sheet and audit notes.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Implement ranking losses and SupCon",
      "details": "Implement ROADMAP, FastAP, SmoothAP and SupCon from permitted sources; record any blocked dependency explicitly.",
      "expected_output": "Implement ROADMAP, FastAP, SmoothAP and SupCon from permitted sources; record any blocked dependency explicitly."
    }
  },
  {
    "table": "tasks",
    "id": "w05-task-04",
    "week_id": "week-05",
    "before": {
      "id": "w05-task-04",
      "week_id": "week-05",
      "position": 4,
      "title": "Freeze corruptions-v1",
      "details": "Verify byte-identical severity zero, query-only application, unchanged tensor shape, and sample-derived seeds. Document any geometry-driven amendment.",
      "expected_output": "Frozen corruption config with hash and amendment record.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Verify every loss configuration",
      "details": "Check values/gradients, edge cases, short development overfits, licenses and registry status for all loss-only methods.",
      "expected_output": "Check values/gradients, edge cases, short development overfits, licenses and registry status for all loss-only methods."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-01",
    "week_id": "week-05",
    "before": {
      "id": "w05-gate-01",
      "week_id": "week-05",
      "position": 1,
      "criterion": "Severity zero is byte-identical and no gallery tensor changes.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Every declared loss method has an auditable source, explicit parameters and passing numerical tests."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-02",
    "week_id": "week-05",
    "before": {
      "id": "w05-gate-02",
      "week_id": "week-05",
      "position": 2,
      "criterion": "Affected proportions, temporal placement, and deterministic hashes pass.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "The same physical batch and 512-dimensional head are used where scientifically applicable."
    }
  },
  {
    "table": "gates",
    "id": "w05-gate-03",
    "week_id": "week-05",
    "before": {
      "id": "w05-gate-03",
      "week_id": "week-05",
      "position": 3,
      "criterion": "Corruptions-v1 is frozen with no amendment or a documented result-blind geometry-only amendment.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Unavailable implementations remain required blockers and are not silently removed."
    }
  },
  {
    "table": "weeks",
    "id": "week-06",
    "week_id": "week-06",
    "before": {
      "id": "week-06",
      "project_id": "pose-embed",
      "number": 6,
      "start_date": "2026-10-19",
      "end_date": "2026-10-25",
      "phase": "Validation",
      "title": "Equal-budget validation I",
      "objective": "Run the same six clean-development trials for each core objective and identify viable settings without touching the novel test.",
      "deliverable": "An equal-budget validation ledger with at least two viable configurations per core method.",
      "risks": [
        "Run duration may exceed the Week 1 estimate.",
        "A method may collapse or require debugging inside the fixed budget.",
        "Accidental access to novel-test manifests would invalidate the lock."
      ],
      "advisor_prompt": "Are the six trials genuinely equal in budget and is the viability rule defined without privileging a method?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Architecture method adaptations",
      "objective": "Adapt every architecture-specific comparison to motion and document departures from the image design.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w06-task-01",
    "week_id": "week-06",
    "before": {
      "id": "w06-task-01",
      "week_id": "week-06",
      "position": 1,
      "title": "Freeze the tuning grid",
      "details": "Write the six shared learning-rate and weight-decay trials, common epoch cap, clean metric, seed, and failure criteria into versioned configs.",
      "expected_output": "Checksummed equal-budget tuning specification.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Adapt DRML, DIML and DiVA",
      "details": "Specify and implement required distribution, local alignment and disentangled branches using compatible motion features.",
      "expected_output": "Specify and implement required distribution, local alignment and disentangled branches using compatible motion features."
    }
  },
  {
    "table": "tasks",
    "id": "w06-task-02",
    "week_id": "week-06",
    "before": {
      "id": "w06-task-02",
      "week_id": "week-06",
      "position": 2,
      "title": "Run first-seed validation",
      "details": "Run all 18 method-by-configuration jobs on clean development data with identical batch manifests and record every attempted run.",
      "expected_output": "Complete first-seed validation result ledger.",
      "required": true,
      "estimate_minutes": 300,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Adapt IBC and S2SD",
      "details": "Implement their required training mechanisms, auxiliaries and supervision, with permitted provenance.",
      "expected_output": "Implement their required training mechanisms, auxiliaries and supervision, with permitted provenance."
    }
  },
  {
    "table": "tasks",
    "id": "w06-task-03",
    "week_id": "week-06",
    "before": {
      "id": "w06-task-03",
      "week_id": "week-06",
      "position": 3,
      "title": "Inspect training health",
      "details": "Check convergence, embedding norms, collapse diagnostics, runtime, memory, and sampler invariants. Reproduce rather than silently discard failures.",
      "expected_output": "Health report and classified failure list.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Adapt all Metrix variants, HIST and MHGL",
      "details": "Preserve method-specific mixing, relation, hierarchy and graph mechanisms; generic scalar substitutes are prohibited.",
      "expected_output": "Preserve method-specific mixing, relation, hierarchy and graph mechanisms; generic scalar substitutes are prohibited."
    }
  },
  {
    "table": "tasks",
    "id": "w06-task-04",
    "week_id": "week-06",
    "before": {
      "id": "w06-task-04",
      "week_id": "week-06",
      "position": 4,
      "title": "Select viable candidates",
      "details": "Apply the predeclared clean-validation rule to retain at least two settings per method for paired multi-seed confirmation.",
      "expected_output": "Candidate list with evidence and no novel-test access.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Implement the matched AVSL comparison",
      "details": "Implement PA + AVSL and Contextual at 1,536 dimensions; document identical dimensions/backbone budgets and architecture costs.",
      "expected_output": "Implement PA + AVSL and Contextual at 1,536 dimensions; document identical dimensions/backbone budgets and architecture costs."
    }
  },
  {
    "table": "gates",
    "id": "w06-gate-01",
    "week_id": "week-06",
    "before": {
      "id": "w06-gate-01",
      "week_id": "week-06",
      "position": 1,
      "criterion": "The equal-budget ledger contains every planned run and classified failure.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Every architecture row is implemented faithfully or remains an explicit blocker with an adaptation decision."
    }
  },
  {
    "table": "gates",
    "id": "w06-gate-02",
    "week_id": "week-06",
    "before": {
      "id": "w06-gate-02",
      "week_id": "week-06",
      "position": 2,
      "criterion": "At least two viable configurations remain for each core method.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Method-specific changes and extra supervision are disclosed; no unpublished shortcut is represented as replication."
    }
  },
  {
    "table": "gates",
    "id": "w06-gate-03",
    "week_id": "week-06",
    "before": {
      "id": "w06-gate-03",
      "week_id": "week-06",
      "position": 3,
      "criterion": "Audit evidence confirms that no novel-test manifest or score was loaded.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "The 1,536-dimensional comparison is kept separate from the 512-dimensional table."
    }
  },
  {
    "table": "weeks",
    "id": "week-07",
    "week_id": "week-07",
    "before": {
      "id": "week-07",
      "project_id": "pose-embed",
      "number": 7,
      "start_date": "2026-10-26",
      "end_date": "2026-11-01",
      "phase": "Lock",
      "title": "Validation II and protocol lock",
      "objective": "Confirm the top candidates across paired seeds and lock every decision before final training and novel evaluation.",
      "deliverable": "Frozen final configs, analysis plan, and protocol-lock hash.",
      "risks": [
        "High seed variance may make the candidate choice unstable.",
        "Late changes can create unequal tuning or accidental test flexibility.",
        "Stretch planning can distract from unresolved core instability."
      ],
      "advisor_prompt": "Are the final hyperparameters, fixed epoch counts, paired seeds, analysis code, and decision to keep or cancel the stretch method documented and frozen?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 2
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Complete coverage and resource gate",
      "objective": "Establish all 26 configurations can run before expensive benchmark selection starts.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w07-task-01",
    "week_id": "week-07",
    "before": {
      "id": "w07-task-01",
      "week_id": "week-07",
      "position": 1,
      "title": "Repeat candidates across seeds",
      "details": "Run the best two clean-validation candidates for each method over all three paired seeds, reusing seed-specific initialization and batch order.",
      "expected_output": "Complete multi-seed candidate matrix.",
      "required": true,
      "estimate_minutes": 240,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Audit the complete paper mapping",
      "details": "Reconcile main tables and appendix, reproducibility scope, equations, licenses and all 26 registry entries.",
      "expected_output": "Reconcile main tables and appendix, reproducibility scope, equations, licenses and all 26 registry entries."
    }
  },
  {
    "table": "tasks",
    "id": "w07-task-02",
    "week_id": "week-07",
    "before": {
      "id": "w07-task-02",
      "week_id": "week-07",
      "position": 2,
      "title": "Select final settings",
      "details": "Choose learning rate, weight decay, and fixed epoch count by the preregistered mean clean-validation rule. Preserve all seed results.",
      "expected_output": "One final config per core method with decision trace.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Run all-method development smoke matrix",
      "details": "Require finite training and retrieval output for every configuration with fixed development data.",
      "expected_output": "Require finite training and retrieval output for every configuration with fixed development data."
    }
  },
  {
    "table": "tasks",
    "id": "w07-task-03",
    "week_id": "week-07",
    "before": {
      "id": "w07-task-03",
      "week_id": "week-07",
      "position": 3,
      "title": "Audit comparison fairness",
      "details": "Verify data, frozen encoder, head, sampler, budget, seeds, evaluator, corruption configs, and failure policy. Confirm test-loader access logs are empty.",
      "expected_output": "Signed fairness and leakage audit.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Freeze physical batches and trial budget",
      "details": "Use measured backward memory across methods; publish equal selection budgets and method-specific grids.",
      "expected_output": "Use measured backward memory across methods; publish equal selection budgets and method-specific grids."
    }
  },
  {
    "table": "tasks",
    "id": "w07-task-04",
    "week_id": "week-07",
    "before": {
      "id": "w07-task-04",
      "week_id": "week-07",
      "position": 4,
      "title": "Lock protocol and stretch config",
      "details": "Hash the final protocol and analysis plan. Predeclare the exact pinned Multi-Similarity-plus-miner setup, but cancel stretch work if core stability is unresolved.",
      "expected_output": "Protocol-lock record and conditional stretch decision.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Reforecast the full study",
      "details": "Measure time/storage and researcher work, and record continuation dates if the December planning horizon is insufficient.",
      "expected_output": "Measure time/storage and researcher work, and record continuation dates if the December planning horizon is insufficient."
    }
  },
  {
    "table": "gates",
    "id": "w07-gate-01",
    "week_id": "week-07",
    "before": {
      "id": "w07-gate-01",
      "week_id": "week-07",
      "position": 1,
      "criterion": "Final core configs are stable across paired seeds and have complete decision traces.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "All 26 configurations pass implementation and licensed-provenance review; unresolved rows block complete replication."
    }
  },
  {
    "table": "gates",
    "id": "w07-gate-02",
    "week_id": "week-07",
    "before": {
      "id": "w07-gate-02",
      "week_id": "week-07",
      "position": 2,
      "criterion": "Final hashes, fairness audit, and analysis plan are recorded before test opening.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Shared settings, full selection budget and resource forecast are fixed before the main validation campaign."
    }
  },
  {
    "table": "gates",
    "id": "w07-gate-03",
    "week_id": "week-07",
    "before": {
      "id": "w07-gate-03",
      "week_id": "week-07",
      "position": 3,
      "criterion": "No unresolved instability remains and the novel-test loader is unused.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "A documented schedule decision preserves the full declared scope rather than forcing a partial benchmark into the old deadline."
    }
  },
  {
    "table": "weeks",
    "id": "week-08",
    "week_id": "week-08",
    "before": {
      "id": "week-08",
      "project_id": "pose-embed",
      "number": 8,
      "start_date": "2026-11-02",
      "end_date": "2026-11-08",
      "phase": "Training",
      "title": "Final core training",
      "objective": "Train all locked core methods on all 100 auxiliary classes with complete, immutable provenance.",
      "deliverable": "Nine checksummed core checkpoints and their complete run manifests.",
      "risks": [
        "GPU interruption can produce partial checkpoints.",
        "A failed run may tempt an unplanned seed replacement.",
        "Incomplete provenance would make paired results unverifiable."
      ],
      "advisor_prompt": "Do the run manifests demonstrate that all nine checkpoints used the locked settings and the predefined failed-run policy?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Equal-budget full-roster selection",
      "objective": "Tune all declared configurations exclusively on the class-disjoint development split.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w08-task-01",
    "week_id": "week-08",
    "before": {
      "id": "w08-task-01",
      "week_id": "week-08",
      "position": 1,
      "title": "Train nine core runs",
      "details": "Train three methods over three paired seeds on all 100 auxiliary classes, using the locked configs and immutable batch manifests.",
      "expected_output": "Nine completed checkpoints and training logs.",
      "required": true,
      "estimate_minutes": 300,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Freeze the tuning ledger",
      "details": "Declare each method trial space, budget, checkpoint rule and tie-break before trials.",
      "expected_output": "Declare each method trial space, budget, checkpoint rule and tie-break before trials."
    }
  },
  {
    "table": "tasks",
    "id": "w08-task-02",
    "week_id": "week-08",
    "before": {
      "id": "w08-task-02",
      "week_id": "week-08",
      "position": 2,
      "title": "Archive run provenance",
      "details": "Record Git, dependency, upstream, model, data, config, device, seed, timing, and output hashes for each run.",
      "expected_output": "Nine complete machine-readable run manifests.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Run the complete development matrix",
      "details": "Execute every budgeted trial and preserve attempts, outcomes and per-method resource use.",
      "expected_output": "Execute every budgeted trial and preserve attempts, outcomes and per-method resource use."
    }
  },
  {
    "table": "tasks",
    "id": "w08-task-03",
    "week_id": "week-08",
    "before": {
      "id": "w08-task-03",
      "week_id": "week-08",
      "position": 3,
      "title": "Apply the failed-run policy",
      "details": "Classify interruptions, numerical failures, and infrastructure failures. Resume or rerun only as allowed by the locked policy and never substitute a favorable seed.",
      "expected_output": "Failure ledger with every retry justified.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Replicate candidates across paired seeds",
      "details": "Use six paired seeds under the declared selection design; account for early engineering trials transparently.",
      "expected_output": "Use six paired seeds under the declared selection design; account for early engineering trials transparently."
    }
  },
  {
    "table": "tasks",
    "id": "w08-task-04",
    "week_id": "week-08",
    "before": {
      "id": "w08-task-04",
      "week_id": "week-08",
      "position": 4,
      "title": "Verify final checkpoints",
      "details": "Load each checkpoint, verify hashes and dimensions, and run a clean fixture evaluation without accessing novel-test scores.",
      "expected_output": "Nine passing checkpoint verification records.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Audit failures and fairness",
      "details": "Classify operational failures and scientific instability, reconcile budgets, and document all deviations.",
      "expected_output": "Classify operational failures and scientific instability, reconcile budgets, and document all deviations."
    }
  },
  {
    "table": "gates",
    "id": "w08-gate-01",
    "week_id": "week-08",
    "before": {
      "id": "w08-gate-01",
      "week_id": "week-08",
      "position": 1,
      "criterion": "All nine core checkpoints load and match recorded checksums.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Every planned selection trial or classified failure is accounted for."
    }
  },
  {
    "table": "gates",
    "id": "w08-gate-02",
    "week_id": "week-08",
    "before": {
      "id": "w08-gate-02",
      "week_id": "week-08",
      "position": 2,
      "criterion": "Every run has complete provenance, logs, and justified failure handling.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "No novel-test loader or score was used for method, epoch or parameter selection."
    }
  },
  {
    "table": "gates",
    "id": "w08-gate-03",
    "week_id": "week-08",
    "before": {
      "id": "w08-gate-03",
      "week_id": "week-08",
      "position": 3,
      "criterion": "No checkpoint was selected or replaced using novel-test outcomes.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Each method has a result-blind selected configuration under the same declared selection policy."
    }
  },
  {
    "table": "weeks",
    "id": "week-09",
    "week_id": "week-09",
    "before": {
      "id": "week-09",
      "project_id": "pose-embed",
      "number": 9,
      "start_date": "2026-11-09",
      "end_date": "2026-11-15",
      "phase": "Evaluation",
      "title": "One-time novel evaluation",
      "objective": "Open the official novel test once and generate the full clean and corrupted result matrix without post-test tuning.",
      "deliverable": "An immutable 180-row core result matrix with query-count and provenance audits.",
      "risks": [
        "A protocol mismatch at test opening can invalidate the preregistration.",
        "Different corruption realizations across methods would break pairing.",
        "Missing or repeated queries can produce misleading aggregate scores."
      ],
      "advisor_prompt": "Does the evaluation log prove a single protocol-locked opening, identical query tensors across methods, and complete reporting for both query definitions?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Freeze protocol and full final roster",
      "objective": "Lock selection, retrieval manifests, statistics and the complete run roster before final retraining.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w09-task-01",
    "week_id": "week-09",
    "before": {
      "id": "w09-task-01",
      "week_id": "week-09",
      "position": 1,
      "title": "Verify the test-opening lock",
      "details": "Validate protocol-v1 hash, timestamp, final configs, checkpoint set, analysis code, and empty prior-access log before enabling the novel-test command.",
      "expected_output": "Signed test-opening event with exact code and protocol hashes.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Freeze the primary retrieval protocol",
      "details": "Bind multi-positive held-out manifests, relevant counts, self/synchronized exclusions, ties and aggregation.",
      "expected_output": "Bind multi-positive held-out manifests, relevant counts, self/synchronized exclusions, ties and aggregation."
    }
  },
  {
    "table": "tasks",
    "id": "w09-task-02",
    "week_id": "week-09",
    "before": {
      "id": "w09-task-02",
      "week_id": "week-09",
      "position": 2,
      "title": "Encode clean and corrupted queries",
      "details": "Evaluate clean plus nine corruption cells for every method and seed against clean anchors, reusing deterministic query tensors across methods.",
      "expected_output": "Checksummed predictions and metrics for all core conditions.",
      "required": true,
      "estimate_minutes": 240,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Freeze statistics and supplementary analyses",
      "details": "Record paired interval construction, multiplicity treatment, one-shot and any corruption/ablation scope before outcomes.",
      "expected_output": "Record paired interval construction, multiplicity treatment, one-shot and any corruption/ablation scope before outcomes."
    }
  },
  {
    "table": "tasks",
    "id": "w09-task-03",
    "week_id": "week-09",
    "before": {
      "id": "w09-task-03",
      "week_id": "week-09",
      "position": 3,
      "title": "Evaluate both query definitions",
      "details": "Calculate top-1, MRR, and R@5 for the deduplicated-primary and exact-official query sets without changing configs or checkpoints.",
      "expected_output": "Complete matrix of 3 methods by 3 seeds by 10 conditions by 2 query definitions.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Lock all method settings and six seeds",
      "details": "Bind 26 selected configurations, initializations, physical batches, augmentation and dependency/source hashes.",
      "expected_output": "Bind 26 selected configurations, initializations, physical batches, augmentation and dependency/source hashes."
    }
  },
  {
    "table": "tasks",
    "id": "w09-task-04",
    "week_id": "week-09",
    "before": {
      "id": "w09-task-04",
      "week_id": "week-09",
      "position": 4,
      "title": "Freeze and audit results",
      "details": "Verify constant query counts, paired sample IDs, complete cells, stable hashes, and no post-test training. Mark the result set immutable.",
      "expected_output": "180-row result matrix and audit report.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Verify no final-test authorization yet",
      "details": "Prove an incomplete final roster cannot open the test; final lock must await every required final checkpoint.",
      "expected_output": "Prove an incomplete final roster cannot open the test; final lock must await every required final checkpoint."
    }
  },
  {
    "table": "gates",
    "id": "w09-gate-01",
    "week_id": "week-09",
    "before": {
      "id": "w09-gate-01",
      "week_id": "week-09",
      "position": 1,
      "criterion": "The novel test was opened under the exact locked protocol and code hashes.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "All scientific decisions and the 156-run roster are hash-bound and recorded before test opening."
    }
  },
  {
    "table": "gates",
    "id": "w09-gate-02",
    "week_id": "week-09",
    "before": {
      "id": "w09-gate-02",
      "week_id": "week-09",
      "position": 2,
      "criterion": "All 180 core rows exist with constant query counts and paired sample identities.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "No unresolved implementation or selection blocker remains in the declared roster."
    }
  },
  {
    "table": "gates",
    "id": "w09-gate-03",
    "week_id": "week-09",
    "before": {
      "id": "w09-gate-03",
      "week_id": "week-09",
      "position": 3,
      "criterion": "No training, tuning, or selective rerun occurred after test opening.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "The priority two-method phase alone cannot authorize novel evaluation."
    }
  },
  {
    "table": "weeks",
    "id": "week-10",
    "week_id": "week-10",
    "before": {
      "id": "week-10",
      "project_id": "pose-embed",
      "number": 10,
      "start_date": "2026-11-16",
      "end_date": "2026-11-22",
      "phase": "Analysis",
      "title": "Locked core analysis",
      "objective": "Turn the immutable result matrix into the preregistered paired effect, uncertainty estimates, complete figures, and defensible conclusions.",
      "deliverable": "Reproducible core analysis, figures, tables, and report outline completed by November 20.",
      "risks": [
        "Treating synchronized views as independent can understate uncertainty.",
        "A clean-accuracy tradeoff can be hidden by reporting degradation alone.",
        "Exploratory per-class patterns can be mistaken for confirmatory results."
      ],
      "advisor_prompt": "Are the clustered paired interval, clean-performance context, and claim language sufficient to support either a positive, null, or negative result?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Train every final configuration",
      "objective": "Retrain all 26 locked configurations on all 100 auxiliary classes with six paired seeds.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w10-task-01",
    "week_id": "week-10",
    "before": {
      "id": "w10-task-01",
      "week_id": "week-10",
      "position": 1,
      "title": "Compute the primary paired effect",
      "details": "Calculate clean-to-corrupted top-1 drops and the equally weighted contextual-minus-contrastive effect across three seeds and nine corruption cells.",
      "expected_output": "Primary estimate and 10,000-replicate performance-cluster bootstrap interval.",
      "required": true,
      "estimate_minutes": 150,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Execute the 156 final runs",
      "details": "Complete 26 configurations by six seeds using locked settings; retain every immutable attempt.",
      "expected_output": "Complete 26 configurations by six seeds using locked settings; retain every immutable attempt."
    }
  },
  {
    "table": "tasks",
    "id": "w10-task-02",
    "week_id": "week-10",
    "before": {
      "id": "w10-task-02",
      "week_id": "week-10",
      "position": 2,
      "title": "Complete secondary analysis",
      "details": "Report clean top-1, MRR, R@5, every seed, every corruption curve, runtime, memory, per-class errors, and both query definitions.",
      "expected_output": "Complete secondary tables with confirmatory and exploratory labels.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Verify checkpoint and run provenance",
      "details": "Validate weights, optimizer settings, batches, initialization and code against selected configurations.",
      "expected_output": "Validate weights, optimizer settings, batches, initialization and code against selected configurations."
    }
  },
  {
    "table": "tasks",
    "id": "w10-task-03",
    "week_id": "week-10",
    "before": {
      "id": "w10-task-03",
      "week_id": "week-10",
      "position": 3,
      "title": "Generate final core figures",
      "details": "Create degradation curves, interval plot, clean-versus-robustness comparison, representative errors, and supporting tables only from immutable outputs.",
      "expected_output": "Publication-ready, script-generated figures and captions.",
      "required": true,
      "estimate_minutes": 150,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Apply the declared failure policy",
      "details": "Retry only documented operational failures in new directories without changing scientific parameters.",
      "expected_output": "Retry only documented operational failures in new directories without changing scientific parameters."
    }
  },
  {
    "table": "tasks",
    "id": "w10-task-04",
    "week_id": "week-10",
    "before": {
      "id": "w10-task-04",
      "week_id": "week-10",
      "position": 4,
      "title": "Write evidence-matched conclusions",
      "details": "Map each conclusion to a preregistered result. Distinguish less degradation from higher retrieval accuracy and report null or negative findings plainly.",
      "expected_output": "Core result narrative and full report outline by November 20.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Complete the full final-run lock",
      "details": "Bind every required checkpoint and manifest only after all final training is finished.",
      "expected_output": "Bind every required checkpoint and manifest only after all final training is finished."
    }
  },
  {
    "table": "gates",
    "id": "w10-gate-01",
    "week_id": "week-10",
    "before": {
      "id": "w10-gate-01",
      "week_id": "week-10",
      "position": 1,
      "criterion": "The primary estimate and 95% paired cluster-bootstrap interval reproduce from immutable results.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "All 156 final runs are present and verified, or the novel test remains sealed."
    }
  },
  {
    "table": "gates",
    "id": "w10-gate-02",
    "week_id": "week-10",
    "before": {
      "id": "w10-gate-02",
      "week_id": "week-10",
      "position": 2,
      "criterion": "Every claim maps to a preregistered result and clean accuracy is reported beside degradation.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Final retraining covers all 100 auxiliary actions and uses no novel-set checkpoint selection."
    }
  },
  {
    "table": "gates",
    "id": "w10-gate-03",
    "week_id": "week-10",
    "before": {
      "id": "w10-gate-03",
      "week_id": "week-10",
      "position": 3,
      "criterion": "All core figures and tables regenerate and the report outline is complete by November 20.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Every final artifact matches the recorded selected setting and complete run-set lock."
    }
  },
  {
    "table": "weeks",
    "id": "week-11",
    "week_id": "week-11",
    "before": {
      "id": "week-11",
      "project_id": "pose-embed",
      "number": 11,
      "start_date": "2026-11-23",
      "end_date": "2026-11-29",
      "phase": "Buffer",
      "title": "Recovery or gated stretch",
      "objective": "Protect the completed core study first, then run the predeclared Multi-Similarity extension only if every core-readiness gate passes.",
      "deliverable": "A verified core recovery record or clearly labeled exploratory Multi-Similarity results.",
      "risks": [
        "Thanksgiving reduces available work time.",
        "Stretch work can consume the buffer needed for core repair.",
        "A new method can invite unplanned tuning after seeing core results."
      ],
      "advisor_prompt": "Have all four stretch-entry checks passed, or should this week remain exclusively a core recovery buffer?",
      "reflection": "",
      "planned_minutes": 240,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Open and evaluate the complete roster",
      "objective": "Open the novel test once only after all 26 configurations and six seeds satisfy the complete lock.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w11-task-01",
    "week_id": "week-11",
    "before": {
      "id": "w11-task-01",
      "week_id": "week-11",
      "position": 1,
      "title": "Assess core readiness",
      "details": "Verify nine checkpoints, full matrices, reproducible figures, and no unresolved failure. If any check fails, use the full week for core recovery.",
      "expected_output": "Signed recovery-or-stretch decision.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Verify the full test-opening lock",
      "details": "Cross-check methods, seeds, runs, gallery/query construction, sources, code and statistical-plan hashes.",
      "expected_output": "Cross-check methods, seeds, runs, gallery/query construction, sources, code and statistical-plan hashes."
    }
  },
  {
    "table": "tasks",
    "id": "w11-task-02",
    "week_id": "week-11",
    "before": {
      "id": "w11-task-02",
      "week_id": "week-11",
      "position": 2,
      "title": "Run the pinned stretch method",
      "details": "Only after a positive entry decision, train three paired Multi-Similarity-plus-miner seeds using the predeclared pinned implementation and existing clean feature caches.",
      "expected_output": "Three checksummed exploratory checkpoints, or a documented cancellation.",
      "required": false,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Evaluate all clean primary cells",
      "details": "Produce the complete 26-by-six multi-positive retrieval matrix and per-query evidence.",
      "expected_output": "Produce the complete 26-by-six multi-positive retrieval matrix and per-query evidence.",
      "required": true
    }
  },
  {
    "table": "tasks",
    "id": "w11-task-03",
    "week_id": "week-11",
    "before": {
      "id": "w11-task-03",
      "week_id": "week-11",
      "position": 3,
      "title": "Evaluate the stretch identically",
      "details": "Apply the locked evaluator and corruption tensors with no new tuning. Preserve the same query definitions and reporting metrics.",
      "expected_output": "Exploratory result matrix, or a documented cancellation.",
      "required": false,
      "estimate_minutes": 30,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Evaluate locked supplementary tasks",
      "details": "Run only predeclared one-shot, corruption, frozen or ablation analyses; preserve their distinct status.",
      "expected_output": "Run only predeclared one-shot, corruption, frozen or ablation analyses; preserve their distinct status.",
      "required": true
    }
  },
  {
    "table": "tasks",
    "id": "w11-task-04",
    "week_id": "week-11",
    "before": {
      "id": "w11-task-04",
      "week_id": "week-11",
      "position": 4,
      "title": "Document the buffer outcome",
      "details": "Record core repairs, stretch status, deviations, and why the primary conclusions remain unchanged.",
      "expected_output": "Complete Week 11 decision and evidence record.",
      "required": true,
      "estimate_minutes": 30,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Freeze all results and failure records",
      "details": "Audit exact matrix coverage, identical query eligibility and dimension grouping without post-test tuning.",
      "expected_output": "Audit exact matrix coverage, identical query eligibility and dimension grouping without post-test tuning."
    }
  },
  {
    "table": "gates",
    "id": "w11-gate-01",
    "week_id": "week-11",
    "before": {
      "id": "w11-gate-01",
      "week_id": "week-11",
      "position": 1,
      "criterion": "The core study remains complete, reproducible, and unchanged by stretch outcomes.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "The opening ledger proves all declared final training and selection preceded the first novel outcome."
    }
  },
  {
    "table": "gates",
    "id": "w11-gate-02",
    "week_id": "week-11",
    "before": {
      "id": "w11-gate-02",
      "week_id": "week-11",
      "position": 2,
      "criterion": "Any stretch result is labeled exploratory and uses only the predeclared configuration.",
      "required": false,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "All 156 clean primary cells have authorized, finite, reproducible metrics and paired sample identities.",
      "required": true
    }
  },
  {
    "table": "gates",
    "id": "w11-gate-03",
    "week_id": "week-11",
    "before": null,
    "values": {
      "id": "w11-gate-03",
      "week_id": "week-11",
      "position": 3,
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "criterion": "No missing method, selective rerun or changed statistical rule is concealed.",
      "project_id": "pose-embed"
    }
  },
  {
    "table": "weeks",
    "id": "week-12",
    "week_id": "week-12",
    "before": {
      "id": "week-12",
      "project_id": "pose-embed",
      "number": 12,
      "start_date": "2026-11-30",
      "end_date": "2026-12-06",
      "phase": "Reproduction",
      "title": "Reproduction and draft",
      "objective": "Prove the project can be reconstructed independently and turn the complete evidence into a full report draft.",
      "deliverable": "A successful fresh-clone reproduction, regenerated results, and a full report draft.",
      "risks": [
        "The working machine may hide undeclared dependencies or paths.",
        "Large licensed artifacts cannot be bundled with the repository.",
        "Writing may expose missing provenance or methods detail late."
      ],
      "advisor_prompt": "Can you follow the methods and evidence trail without oral context, and which argument or limitation needs the most revision?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 2
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Analysis and independent reproduction",
      "objective": "Compute the preregistered paired comparisons and regenerate complete results from immutable artifacts.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w12-task-01",
    "week_id": "week-12",
    "before": {
      "id": "w12-task-01",
      "week_id": "week-12",
      "position": 1,
      "title": "Reconstruct from a fresh clone",
      "details": "Install pinned dependencies, fetch exact upstream sources, configure external data roots, and verify manifests on a clean checkout.",
      "expected_output": "Fresh-clone environment and dependency audit.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Compute primary and broad paired comparisons",
      "details": "Report Contextual versus Contrastive first, then all declared comparators with the frozen multiplicity rule.",
      "expected_output": "Report Contextual versus Contrastive first, then all declared comparators with the frozen multiplicity rule."
    }
  },
  {
    "table": "tasks",
    "id": "w12-task-02",
    "week_id": "week-12",
    "before": {
      "id": "w12-task-02",
      "week_id": "week-12",
      "position": 2,
      "title": "Run the CPU debug pipeline",
      "details": "Execute parsing, feature fixture, each loss, training, evaluation, and report generation through one documented debug command.",
      "expected_output": "Passing end-to-end CPU smoke run.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Report every metric and resource cost",
      "details": "Publish R@1/2/4/8, mAP, mAP@R, six-seed variation, failures and compute within each dimension group.",
      "expected_output": "Publish R@1/2/4/8, mAP, mAP@R, six-seed variation, failures and compute within each dimension group."
    }
  },
  {
    "table": "tasks",
    "id": "w12-task-03",
    "week_id": "week-12",
    "before": {
      "id": "w12-task-03",
      "week_id": "week-12",
      "position": 3,
      "title": "Regenerate results from archives",
      "details": "Rebuild final tables and figures from explicit immutable run manifests and compare output checksums with the Week 10 release candidates.",
      "expected_output": "Reproduction report with matching or explained hashes.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Reproduce tables from a clean checkout",
      "details": "Verify environment, source records and immutable artifact hashes independently.",
      "expected_output": "Verify environment, source records and immutable artifact hashes independently."
    }
  },
  {
    "table": "tasks",
    "id": "w12-task-04",
    "week_id": "week-12",
    "before": {
      "id": "w12-task-04",
      "week_id": "week-12",
      "position": 4,
      "title": "Write the full report draft",
      "details": "Complete methods, results, limitations, compute, failure handling, deviations, and negative findings. Link every figure to its generating command.",
      "expected_output": "Complete report draft archived with its evidence.",
      "required": true,
      "estimate_minutes": 150,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Write evidence-matched findings",
      "details": "Describe positive, null or negative results and motion-adaptation limitations without universal claims.",
      "expected_output": "Describe positive, null or negative results and motion-adaptation limitations without universal claims."
    }
  },
  {
    "table": "gates",
    "id": "w12-gate-01",
    "week_id": "week-12",
    "before": {
      "id": "w12-gate-01",
      "week_id": "week-12",
      "position": 1,
      "criterion": "A fresh clone installs and completes the documented CPU debug pipeline.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "All tables and intervals regenerate from authorized per-query results."
    }
  },
  {
    "table": "gates",
    "id": "w12-gate-02",
    "week_id": "week-12",
    "before": {
      "id": "w12-gate-02",
      "week_id": "week-12",
      "position": 2,
      "criterion": "Final tables and figures regenerate from archived immutable outputs.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Claims respect the locked multiplicity rule and distinguish 512 versus 1,536 dimensions."
    }
  },
  {
    "table": "gates",
    "id": "w12-gate-03",
    "week_id": "week-12",
    "before": {
      "id": "w12-gate-03",
      "week_id": "week-12",
      "position": 3,
      "criterion": "A complete report draft is recorded and reviewed against the evidence.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Every method, seed, failure, deviation and supplementary analysis is reported."
    }
  },
  {
    "table": "weeks",
    "id": "week-13",
    "week_id": "week-13",
    "before": {
      "id": "week-13",
      "project_id": "pose-embed",
      "number": 13,
      "start_date": "2026-12-07",
      "end_date": "2026-12-13",
      "phase": "Communication",
      "title": "Final communication",
      "objective": "Resolve documented review findings and package the study so its question, evidence, limits, and reproduction path stand on their own.",
      "deliverable": "Final report, poster or slides, abstract, captions, source ledger, and reproducibility walkthrough.",
      "risks": [
        "Late feedback may expand beyond correction into a new analysis request.",
        "Visual summaries can overstate findings when space is tight.",
        "The artifact inventory may expose missing attribution or licenses."
      ],
      "advisor_prompt": "Does the final package communicate the result and its limits accurately, and are all requested corrections complete without adding post-hoc analysis?",
      "reflection": "",
      "planned_minutes": 480,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 2
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Report and evidence package",
      "objective": "Present the motion replication with complete provenance and explicit differences from the image paper.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w13-task-01",
    "week_id": "week-13",
    "before": {
      "id": "w13-task-01",
      "week_id": "week-13",
      "position": 1,
      "title": "Resolve documented review findings",
      "details": "Classify each comment as correction, clarification, limitation, or new analysis. Complete the first three and defer unplanned analysis to future work after December 10.",
      "expected_output": "Resolved feedback log and final report text.",
      "required": true,
      "estimate_minutes": 180,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Write the full replication report",
      "details": "Map every image-paper method to its motion adaptation, source and evidence.",
      "expected_output": "Map every image-paper method to its motion adaptation, source and evidence."
    }
  },
  {
    "table": "tasks",
    "id": "w13-task-02",
    "week_id": "week-13",
    "before": {
      "id": "w13-task-02",
      "week_id": "week-13",
      "position": 2,
      "title": "Finalize poster or slides",
      "details": "Present the research question, controlled comparison, corruption design, primary effect, clean tradeoff, limitations, and reproduction path without selective results.",
      "expected_output": "Final publication-ready poster or slide deck.",
      "required": true,
      "estimate_minutes": 120,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Resolve documented review findings",
      "details": "Correct reproducibility or presentation defects without adding outcome-driven analyses.",
      "expected_output": "Correct reproducibility or presentation defects without adding outcome-driven analyses."
    }
  },
  {
    "table": "tasks",
    "id": "w13-task-03",
    "week_id": "week-13",
    "before": {
      "id": "w13-task-03",
      "week_id": "week-13",
      "position": 3,
      "title": "Complete the evidence package",
      "details": "Finalize the abstract, captions, source ledger, third-party notices, artifact inventory, deviations, and commands behind every result.",
      "expected_output": "Self-contained documented experiment package.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Prepare poster or slides",
      "details": "Explain the question, full comparison, uncertainty and limits clearly.",
      "expected_output": "Explain the question, full comparison, uncertainty and limits clearly."
    }
  },
  {
    "table": "tasks",
    "id": "w13-task-04",
    "week_id": "week-13",
    "before": {
      "id": "w13-task-04",
      "week_id": "week-13",
      "position": 4,
      "title": "Run the evidence walkthrough",
      "details": "Use the public tracker to walk through weeks, evidence, gates, conclusions, limitations, and remaining archive work. Record final corrections.",
      "expected_output": "Completed walkthrough and bounded correction list.",
      "required": true,
      "estimate_minutes": 90,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Package permitted reproduction material",
      "details": "Include source, configs, manifests, compact results and instructions while excluding licensed inputs and checkpoints.",
      "expected_output": "Include source, configs, manifests, compact results and instructions while excluding licensed inputs and checkpoints."
    }
  },
  {
    "table": "gates",
    "id": "w13-gate-01",
    "week_id": "week-13",
    "before": {
      "id": "w13-gate-01",
      "week_id": "week-13",
      "position": 1,
      "criterion": "Final report and poster or slides are understandable without oral explanation.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "The report distinguishes paper reproduction, motion adaptation and supplementary analyses."
    }
  },
  {
    "table": "gates",
    "id": "w13-gate-02",
    "week_id": "week-13",
    "before": {
      "id": "w13-gate-02",
      "week_id": "week-13",
      "position": 2,
      "criterion": "Documented review findings are resolved or explicitly deferred as future work.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 2,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Every claim and comparison maps to a complete locked result."
    }
  },
  {
    "table": "gates",
    "id": "w13-gate-03",
    "week_id": "week-13",
    "before": {
      "id": "w13-gate-03",
      "week_id": "week-13",
      "position": 3,
      "criterion": "No opportunistic post-test analysis was introduced after classes ended.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "The public evidence package is license-safe and reproducible."
    }
  },
  {
    "table": "weeks",
    "id": "week-14",
    "week_id": "week-14",
    "before": {
      "id": "week-14",
      "project_id": "pose-embed",
      "number": 14,
      "start_date": "2026-12-14",
      "end_date": "2026-12-18",
      "phase": "Handoff",
      "title": "Handoff and archive",
      "objective": "Close the project with a verified release, recoverable public tracker, permitted artifacts, and an honest retrospective.",
      "deliverable": "Tagged release, verified backups, final tracker export, reproduction smoke result, and future-work backlog.",
      "risks": [
        "Finals-week availability is limited.",
        "Licensed data or model weights can accidentally enter an archive.",
        "A backup can appear successful while containing fallback rather than live data."
      ],
      "advisor_prompt": "Is the handoff complete, appropriately licensed, reproducible, and clear about deviations and future work?",
      "reflection": "",
      "planned_minutes": 240,
      "actual_minutes": 0,
      "state": "planned",
      "closed_at": null,
      "version": 1
    },
    "values": {
      "phase": "Motion replication v2",
      "title": "Archive or document continuation",
      "objective": "Finish the verified study or explicitly carry unfinished required work beyond this provisional horizon.",
      "deliverable": "Documented completion evidence for this phase, or a visible blocker and dated continuation.",
      "risks": [
        "Dates and effort are provisional until the all-method resource gate passes.",
        "Method implementation, license or resource blockers cannot be resolved by silent omission."
      ],
      "advisor_prompt": "Does the evidence satisfy this phase while preserving all declared methods and the novel-test seal?"
    }
  },
  {
    "table": "tasks",
    "id": "w14-task-01",
    "week_id": "week-14",
    "before": {
      "id": "w14-task-01",
      "week_id": "week-14",
      "position": 1,
      "title": "Create the final release",
      "details": "Verify the release commit, changelog, report, configs, manifests, summary results, and notices, then create the final tag.",
      "expected_output": "Immutable final source release and tag.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Assess completion against full scope",
      "details": "Use the 26-configuration coverage ledger; missing methods or final runs remain incomplete.",
      "expected_output": "Use the 26-configuration coverage ledger; missing methods or final runs remain incomplete."
    }
  },
  {
    "table": "tasks",
    "id": "w14-task-02",
    "week_id": "week-14",
    "before": {
      "id": "w14-task-02",
      "week_id": "week-14",
      "position": 2,
      "title": "Archive permitted artifacts",
      "details": "Archive run manifests, small summary results, report sources, and reproduction instructions. Explicitly exclude licensed data, checkpoints, credentials, and caches.",
      "expected_output": "Checksum-verified, license-safe archive.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Record a dated continuation if needed",
      "details": "Extend the plan with measured estimates before opening the test if required work exceeds this horizon.",
      "expected_output": "Extend the plan with measured estimates before opening the test if required work exceeds this horizon."
    }
  },
  {
    "table": "tasks",
    "id": "w14-task-03",
    "week_id": "week-14",
    "before": {
      "id": "w14-task-03",
      "week_id": "week-14",
      "position": 3,
      "title": "Export and back up the tracker",
      "details": "Export public progress plus the owner-only activity history. Confirm the export source is Supabase and verify independent copies.",
      "expected_output": "Dated JSON and Markdown exports with verified backups.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Archive source and permitted evidence",
      "details": "Preserve releases, histories, run manifests and compact outputs without overwriting prior artifacts.",
      "expected_output": "Preserve releases, histories, run manifests and compact outputs without overwriting prior artifacts."
    }
  },
  {
    "table": "tasks",
    "id": "w14-task-04",
    "week_id": "week-14",
    "before": {
      "id": "w14-task-04",
      "week_id": "week-14",
      "position": 4,
      "title": "Run final smoke and retrospective",
      "details": "Run the fresh-clone smoke path, verify the public site, record protocol deviations and lessons, and create a bounded future-work backlog.",
      "expected_output": "Final verification record and retrospective.",
      "required": true,
      "estimate_minutes": 60,
      "state": "todo",
      "completion_note": "",
      "evidence_url": null,
      "completed_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "title": "Export and verify the tracker",
      "details": "Produce public-safe exports, check live protocol/schedule consistency and record actual researcher time.",
      "expected_output": "Produce public-safe exports, check live protocol/schedule consistency and record actual researcher time."
    }
  },
  {
    "table": "gates",
    "id": "w14-gate-01",
    "week_id": "week-14",
    "before": {
      "id": "w14-gate-01",
      "week_id": "week-14",
      "position": 1,
      "criterion": "Release, archive, and tracker exports are checksummed and independently backed up.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Completion requires the entire declared benchmark and its report, not merely reaching December 18."
    }
  },
  {
    "table": "gates",
    "id": "w14-gate-02",
    "week_id": "week-14",
    "before": {
      "id": "w14-gate-02",
      "week_id": "week-14",
      "position": 2,
      "criterion": "Licensed data, checkpoints, secrets, and caches are absent from the release.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Unfinished work is visible with a dated continuation and preserved novel-test seal."
    }
  },
  {
    "table": "gates",
    "id": "w14-gate-03",
    "week_id": "week-14",
    "before": {
      "id": "w14-gate-03",
      "week_id": "week-14",
      "position": 3,
      "criterion": "Final smoke reproduction and public tracker checks pass.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Source, permitted artifacts and tracker exports are independently recoverable."
    }
  },
  {
    "table": "gates",
    "id": "w14-gate-04",
    "week_id": "week-14",
    "before": {
      "id": "w14-gate-04",
      "week_id": "week-14",
      "position": 4,
      "criterion": "Deviations, limitations, retrospective, and future work are recorded.",
      "required": true,
      "state": "pending",
      "evidence": "",
      "waiver_reason": "",
      "decided_at": null,
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "criterion": "Researcher time and retrospective are recorded without invented hours."
    }
  },
  {
    "table": "sources",
    "id": "source-contextual",
    "week_id": null,
    "before": {
      "id": "source-contextual",
      "title": "Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization",
      "authors": "Liao et al.",
      "year": 2023,
      "canonical_url": "https://proceedings.mlr.press/v202/liao23b.html",
      "purpose": "Defines the contextual objective, controlled metric-learning comparisons, and the limits of the original robustness evidence.",
      "verified_at": "2026-09-06",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "sources",
    "id": "source-motionbert",
    "week_id": null,
    "before": {
      "id": "source-motionbert",
      "title": "MotionBERT: A Unified Perspective on Learning Human Motion Representations",
      "authors": "Zhu et al.",
      "year": 2023,
      "canonical_url": "https://openaccess.thecvf.com/content/ICCV2023/html/Zhu_MotionBERT_A_Unified_Perspective_on_Learning_Human_Motion_Representations_ICCV_2023_paper.html",
      "purpose": "Specifies the pretrained pose encoder and its NTU RGB+D 120 one-shot evaluation context.",
      "verified_at": "2026-09-06",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "sources",
    "id": "source-maskclr",
    "week_id": null,
    "before": {
      "id": "source-maskclr",
      "title": "MaskCLR: Attention-Guided Contrastive Learning for Robust Action Representation Learning",
      "authors": "Abdelfattah et al.",
      "year": 2024,
      "canonical_url": "https://openaccess.thecvf.com/content/CVPR2024/html/Abdelfattah_MaskCLR_Attention-Guided_Contrastive_Learning_for_Robust_Action_Representation_Learning_CVPR_2024_paper.html",
      "purpose": "Grounds the use of Gaussian noise and joint or frame masking as pose-robustness stress tests.",
      "verified_at": "2026-09-06",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "sources",
    "id": "source-skeleton-dml",
    "week_id": null,
    "before": {
      "id": "source-skeleton-dml",
      "title": "Skeleton-DML: Deep Metric Learning for Skeleton-Based One-Shot Action Recognition",
      "authors": "Memmesheimer et al.",
      "year": 2022,
      "canonical_url": "https://openaccess.thecvf.com/content/WACV2022/html/Memmesheimer_Skeleton-DML_Deep_Metric_Learning_for_Skeleton-Based_One-Shot_Action_Recognition_WACV_2022_paper.html",
      "purpose": "Provides precedent for class-disjoint development validation within the NTU one-shot setup.",
      "verified_at": "2026-09-06",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "sources",
    "id": "source-ntu",
    "week_id": null,
    "before": {
      "id": "source-ntu",
      "title": "NTU RGB+D 120 dataset and one-shot protocol",
      "authors": "Liu et al.",
      "year": 2019,
      "canonical_url": "https://github.com/shahroudy/NTURGB-D/blob/master/README.md",
      "purpose": "Canonical dataset access, action indexing, and one-shot split reference.",
      "verified_at": "2026-09-06",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "sources",
    "id": "source-prospectus",
    "week_id": null,
    "before": {
      "id": "source-prospectus",
      "title": "Robust Human-Motion Retrieval from Noisy Pose Sequences",
      "authors": "Giacomo Cappelletto",
      "year": 2026,
      "canonical_url": "https://github.com/JJCAPPE/pose-embedding",
      "purpose": "Binding local prospectus and scope authority for the project.",
      "verified_at": "2026-09-06",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "sources",
    "id": "source-bu-calendar",
    "week_id": null,
    "before": {
      "id": "source-bu-calendar",
      "title": "Boston University semester dates",
      "authors": "Boston University",
      "year": 2026,
      "canonical_url": "https://www.bu.edu/reg/calendars/semester/",
      "purpose": "Defines holiday, class-end, study-period, and final-exam constraints on the schedule.",
      "verified_at": "2026-09-06",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {}
  },
  {
    "table": "sources",
    "id": "source-benchmark-v2",
    "week_id": null,
    "before": null,
    "values": {
      "id": "source-benchmark-v2",
      "title": "Motion retrieval v2 method registry and protocol",
      "authors": "Pose Embed independent research",
      "year": 2026,
      "canonical_url": "https://github.com/JJCAPPE/pose-embedding/blob/main/configs/benchmark-methods.v2.json",
      "purpose": "All 26 required configurations, primary sources, implementation status and explicit adaptation blockers; see docs/protocol/protocol-v2.md.",
      "verified_at": "2026-09-24",
      "project_id": "pose-embed"
    }
  },
  {
    "table": "week_sources",
    "id": "week-01:source-prospectus",
    "week_id": "week-01",
    "before": {
      "week_id": "week-01",
      "source_id": "source-prospectus",
      "purpose": "Lock the final scientific scope and claims.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {},
    "source_id": "source-prospectus"
  },
  {
    "table": "week_sources",
    "id": "week-01:source-ntu",
    "week_id": "week-01",
    "before": {
      "week_id": "week-01",
      "source_id": "source-ntu",
      "purpose": "Verify licensed data and official one-shot inputs.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {},
    "source_id": "source-ntu"
  },
  {
    "table": "week_sources",
    "id": "week-02:source-ntu",
    "week_id": "week-02",
    "before": {
      "week_id": "week-02",
      "source_id": "source-ntu",
      "purpose": "Implement official action and exemplar semantics.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {},
    "source_id": "source-ntu"
  },
  {
    "table": "week_sources",
    "id": "week-02:source-skeleton-dml",
    "week_id": "week-02",
    "before": {
      "week_id": "week-02",
      "source_id": "source-skeleton-dml",
      "purpose": "Apply class-disjoint development-validation precedent.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {},
    "source_id": "source-skeleton-dml"
  },
  {
    "table": "week_sources",
    "id": "week-03:source-motionbert",
    "week_id": "week-03",
    "before": {
      "week_id": "week-03",
      "source_id": "source-motionbert",
      "purpose": "Reproduce the frozen encoder and one-shot embedding head interface.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {},
    "source_id": "source-motionbert"
  },
  {
    "table": "week_sources",
    "id": "week-04:source-contextual",
    "week_id": "week-04",
    "before": {
      "week_id": "week-04",
      "source_id": "source-contextual",
      "purpose": "Implement and validate the contextual objective and controlled comparators.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {},
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-05:source-maskclr",
    "week_id": "week-05",
    "before": {
      "week_id": "week-05",
      "source_id": "source-maskclr",
      "purpose": "Ground corruption families and visual validation practice.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Supplementary corruption context only; implement the primary loss roster from the v2 registry.",
      "priority": "recommended"
    },
    "source_id": "source-maskclr"
  },
  {
    "table": "week_sources",
    "id": "week-06:source-contextual",
    "week_id": "week-06",
    "before": {
      "week_id": "week-06",
      "source_id": "source-contextual",
      "purpose": "Maintain equal-budget objective comparisons.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Audit every architecture-specific comparison and its motion adaptation."
    },
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-07:source-contextual",
    "week_id": "week-07",
    "before": {
      "week_id": "week-07",
      "source_id": "source-contextual",
      "purpose": "Pin the conditional Multi-Similarity configuration before test access.",
      "priority": "recommended",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Verify all 26 declared configurations, licenses and resource feasibility before full selection.",
      "priority": "required"
    },
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-09:source-ntu",
    "week_id": "week-09",
    "before": {
      "week_id": "week-09",
      "source_id": "source-ntu",
      "purpose": "Preserve exact-official one-shot comparability.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Freeze multi-positive held-out identities while retaining the official one-shot task as supplementary."
    },
    "source_id": "source-ntu"
  },
  {
    "table": "week_sources",
    "id": "week-10:source-prospectus",
    "week_id": "week-10",
    "before": {
      "week_id": "week-10",
      "source_id": "source-prospectus",
      "purpose": "Match claims to the preregistered primary effect.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Preserve the historical prospectus; v2 protocol and complete final roster supersede its narrow scope.",
      "priority": "recommended"
    },
    "source_id": "source-prospectus"
  },
  {
    "table": "week_sources",
    "id": "week-11:source-contextual",
    "week_id": "week-11",
    "before": {
      "week_id": "week-11",
      "source_id": "source-contextual",
      "purpose": "Run the gated stretch with the controlled published configuration.",
      "priority": "recommended",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Evaluate every locked method; the v1 post-core Multi-Similarity exception does not apply.",
      "priority": "required"
    },
    "source_id": "source-contextual"
  },
  {
    "table": "week_sources",
    "id": "week-12:source-motionbert",
    "week_id": "week-12",
    "before": {
      "week_id": "week-12",
      "source_id": "source-motionbert",
      "purpose": "Audit method and encoder reporting in the draft.",
      "priority": "recommended",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {},
    "source_id": "source-motionbert"
  },
  {
    "table": "week_sources",
    "id": "week-13:source-bu-calendar",
    "week_id": "week-13",
    "before": {
      "week_id": "week-13",
      "source_id": "source-bu-calendar",
      "purpose": "Respect the end-of-classes analysis freeze.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Treat current semester dates as a planning horizon and record any necessary continuation.",
      "priority": "recommended"
    },
    "source_id": "source-bu-calendar"
  },
  {
    "table": "week_sources",
    "id": "week-14:source-prospectus",
    "week_id": "week-14",
    "before": {
      "week_id": "week-14",
      "source_id": "source-prospectus",
      "purpose": "Verify the final release against the binding scope.",
      "priority": "required",
      "version": 1,
      "project_id": "pose-embed"
    },
    "values": {
      "purpose": "Archive the historical prospectus alongside the superseding v2 protocol.",
      "priority": "recommended"
    },
    "source_id": "source-prospectus"
  },
  {
    "table": "week_sources",
    "id": "week-04:source-benchmark-v2",
    "week_id": "week-04",
    "before": null,
    "values": {
      "week_id": "week-04",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-05:source-benchmark-v2",
    "week_id": "week-05",
    "before": null,
    "values": {
      "week_id": "week-05",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-06:source-benchmark-v2",
    "week_id": "week-06",
    "before": null,
    "values": {
      "week_id": "week-06",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-07:source-benchmark-v2",
    "week_id": "week-07",
    "before": null,
    "values": {
      "week_id": "week-07",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-08:source-benchmark-v2",
    "week_id": "week-08",
    "before": null,
    "values": {
      "week_id": "week-08",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-09:source-benchmark-v2",
    "week_id": "week-09",
    "before": null,
    "values": {
      "week_id": "week-09",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-10:source-benchmark-v2",
    "week_id": "week-10",
    "before": null,
    "values": {
      "week_id": "week-10",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-11:source-benchmark-v2",
    "week_id": "week-11",
    "before": null,
    "values": {
      "week_id": "week-11",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-12:source-benchmark-v2",
    "week_id": "week-12",
    "before": null,
    "values": {
      "week_id": "week-12",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-13:source-benchmark-v2",
    "week_id": "week-13",
    "before": null,
    "values": {
      "week_id": "week-13",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
  },
  {
    "table": "week_sources",
    "id": "week-14:source-benchmark-v2",
    "week_id": "week-14",
    "before": null,
    "values": {
      "week_id": "week-14",
      "source_id": "source-benchmark-v2",
      "purpose": "Use the complete v2 roster and sealed-test requirements for this phase.",
      "priority": "required",
      "project_id": "pose-embed"
    },
    "source_id": "source-benchmark-v2"
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
    raise notice 'pose-embed is not seeded; import research-plan.v2.json';
    return;
  end if;

  -- A plan rewrite is never an implicit reopen. Lock every affected parent.
  for parent_id in
    select distinct value->>'week_id' from jsonb_array_elements(edits)
    where value->>'week_id' is not null and value->'values' <> '{}'::jsonb
  loop
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
    else
      execute format('select to_jsonb(t) from public.%I t where id = $1 for update', edit->>'table')
        into current_row using edit->>'id';
    end if;

    if edit->'before' = 'null'::jsonb then
      expected_row := edit->'values' || jsonb_build_object('version', 1);
      if current_row is not null then
        if current_row @> expected_row then continue; end if;
        raise exception using errcode = '40001',
          message = edit->>'id' || ' already exists with different content';
      end if;
      select string_agg(format('%I', key), ', ' order by key),
             string_agg(format('v.%I', key), ', ' order by key)
        into columns_sql, assignments from jsonb_object_keys(expected_row) key;
      execute format('insert into public.%I (%s) select %s from jsonb_populate_record(null::public.%I, $1) v',
        edit->>'table', columns_sql, assignments, edit->>'table') using expected_row;
      continue;
    end if;

    expected_version := (edit->'before'->>'version')::integer;
    expected_row := edit->'before' || edit->'values' || jsonb_build_object(
      'version', expected_version + case when edit->'values' = '{}'::jsonb then 0 else 1 end);
    -- Full content and resulting version must match for an exact idempotent replay.
    if current_row @> expected_row then continue; end if;
    if current_row is null or not (current_row @> (edit->'before')) then
      raise exception using errcode = '40001',
        message = edit->>'id' || ' changed; refusing to overwrite live progress';
    end if;
    if edit->'values' = '{}'::jsonb then continue; end if;
    select string_agg(format('%I = v.%I', key, key), ', ' order by key)
      into assignments from jsonb_object_keys(edit->'values') key;
    if edit->>'table' = 'week_sources' then
      execute format('update public.week_sources t set %s from jsonb_populate_record(null::public.week_sources, $1) v where t.project_id = ''pose-embed'' and t.week_id = $2 and t.source_id = $3 and t.version = $4', assignments)
        using edit->'values', edit->>'week_id', edit->>'source_id', expected_version;
    else
      execute format('update public.%I t set %s from jsonb_populate_record(null::public.%I, $1) v where t.id = $2 and t.version = $3',
        edit->>'table', assignments, edit->>'table')
        using edit->'values', edit->>'id', expected_version;
    end if;
    get diagnostics changed_rows = row_count;
    if changed_rows <> 1 then
      raise exception using errcode = '40001', message = edit->>'id' || ' could not be updated';
    end if;
  end loop;
end
$migration$;
