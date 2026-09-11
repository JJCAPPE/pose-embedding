# Week 1 approval and access record

Complete this public-safe record before closing Week 1. Keep credentials,
licensed file URLs, private correspondence, and data outside Git; link only to
evidence that may safely be shared with the advisor.

## Protocol approval

- Protocol ID: `protocol-v1`
- Protocol digest: `<run pose-embed protocol verify and paste sha256>`
- Evaluation-plan digest: `<record when the final-test lock is created>`
- Advisor decision: `<approved / approved with conditions / pending>`
- Decision date and timezone: `<RFC 3339 timestamp>`
- Public-safe evidence or meeting record: `<URL or repository path>`
- Conditions or unresolved questions: `<text>`

Approval covers the research question, auxiliary/novel split, synchronized-view
exclusion, corruption protocol, primary estimand and claim rule, tuning budget,
test-opening rule, and failed-run policy.

## BU determination

- Office or process consulted: `<name>`
- Determination/reference: `<public-safe identifier>`
- Decision date: `<YYYY-MM-DD>`
- Conditions relevant to this repository: `<text>`
- Private evidence location outside the public tracker: `<local description>`

Only BU personnel may provide the institutional determination. This template
records it; it is not itself an approval.

## Licensed input inventory

Review the
[NTU RGB+D release agreement reference](../compliance/ntu-rgbd-release-agreement.md)
and its linked current request form before recording access. The checked-in
reference is not proof of acceptance.

| Input | Authorized source | Local path below `POSE_EMBED_DATA_ROOT` | Bytes | SHA-256 | Verified UTC |
|---|---|---|---:|---|---|
| NTU RGB+D 120 HRNet pose files | `<source>` | `<relative path>` | `<bytes>` | `<sha256>` | `<timestamp>` |
| Official one-shot manifest | `<source>` | `<relative path>` | `<bytes>` | `<sha256>` | `<timestamp>` |
| MotionBERT checkpoint | `<source/config ID>` | `<relative path>` | `<bytes>` | `<sha256>` | `<timestamp>` |

Do not commit the listed inputs or an authenticated download URL.

## GPU and scheduler profile

- Host or cluster label: `<non-secret label>`
- Scheduler and version: `<value>`
- GPU model / VRAM: `<value>`
- Driver / CUDA compatibility: `<value>`
- Storage quota and current free space: `<value>`
- Wall-time, queue, and concurrent-job limits: `<value>`

| Physical batch | Input shape/dtype | Peak VRAM | Median forward time | Repeats | Decision |
|---:|---|---:|---:|---:|---|
| 32 | `<value>` | `<value>` | `<value>` | `<value>` | `<retain/fail>` |
| 64 | `<value>` | `<value>` | `<value>` | `<value>` | `<retain/fail>` |

The default remains physical `P=8`, `K=4`, batch 32 unless every core method
fits at 64. Gradient accumulation does not establish contextual-objective batch
equivalence.

## Closure checklist

- [ ] Protocol approval and digest are recorded.
- [ ] BU determination is recorded.
- [ ] All authorized inputs are readable and checksummed.
- [ ] The pinned MotionBERT adapter/parity gate is complete.
- [ ] GPU profile supports a feasible physical batch size.
- [ ] Tracker tasks, actual hours, blockers, evidence, and reflection are current.
