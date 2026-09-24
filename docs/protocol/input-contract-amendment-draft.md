# Input-contract amendment — draft for advisor review

Status: **DRAFT — not approved and not effective**. Prepared 2026-09-24.
This document proposes a narrow correction to the locked input contract. It
does not change the protocol, configuration, code, approval record, or test
seal, and it does not constitute a BU governance determination.

Current protocol: `protocol-v1`, canonical SHA-256
`12cf4d9a322f5bd5ea76fb2d9ffc070a6a2681fe8474a05cff1f62b6e43368e2`.

## Reason for the proposed amendment

The [verified input inventory](week-1-input-inventory.md) and
[manifest audit](ntu-manifest-audit.v1.md) account for the nominal 114,480 NTU
RGB+D 120 captures as 113,945 usable HRNet annotations and 535 entries in the
dataset authors' missing-skeleton list. The two sets have no overlapping IDs.
The usable aggregate contains all 120 actions and all 20 official exemplars.

The current protocol requires 114,480 source-inventory rows backed by
per-sample files. The verified release is an aggregate containing the usable
annotations. Additional downloads of Kinect skeletons do not resolve that
contract: Kinect 25-joint 3D skeletons are a different representation from the
specified HRNet COCO-17 2D coordinates and confidence scores. Missing samples
must not be represented by fabricated poses or placeholder inventory rows.

## Proposed decision wording

> Approve an input-contract amendment, before novel-test opening and without
> using novel-test outcomes, that defines the complete usable HRNet source
> inventory as exactly 113,945 unique annotations. Account separately for the
> 535 officially excluded nominal captures using the hash-pinned missing-skeleton
> list below, so that usable and excluded IDs are disjoint and together account
> for 114,480 nominal captures. At initial test opening, verify the physical
> aggregate and missing-list files by their byte counts and SHA-256 digests,
> revalidate the aggregate annotations and exact derived inventory, and bind
> both inputs through the evaluation plan and immutable opening ledger. This
> replaces the requirement for 114,480 physical per-sample pose files. All
> other scientific controls and test-opening prerequisites remain unchanged.

The wording above is a proposal for an authorized advisor decision; it is not
an assertion that approval has been given.

## Exact proposed input binding

Paths are relative to `POSE_EMBED_DATA_ROOT`. Licensed inputs remain outside
Git; this document contains only public-safe metadata.

| Physical input | Bytes | SHA-256 |
| --- | ---: | --- |
| `ntu120_hrnet.pkl` | 1,238,461,428 | `aaf1f928b4629fa9a0850528d43fdd8d920532805d16672bfdda78085b649df8` |
| `provenance/sources/NTU_RGBD120_samples_with_missing_skeletons.txt` | 11,451 | `ab14fe64e89be63d2b08141713fcc31f6ebc7b01955009c3585d8d3367e0facc` |

The official missing list is pinned to NTURGB-D commit
`ac2ebc87e6e9777ea6bac67e65e53b325b903f74`. Source URLs and verification results
are recorded in `data/manifests/ntu120-hrnet.v1.json`.

The existing 113,945-row `source-inventory.jsonl` has SHA-256
`e0ab842fe2a62b50ff7205d0f8658fad373a03c5b29527c281a2db0225ea0058`.
The manifest audit records the seven derived manifests and their digests:
76,013 development-training, 18,988 development-validation, 95,001 final-training,
18,944 official-novel, 20 anchor, 18,884 primary-query, and 18,924 official-query
rows. These counts describe data identities, not retrieval outcomes. Physical
source-file count would be **2**; usable source-row count would be **113,945**.

## Controls that remain unchanged

- The frozen generic MotionBERT encoder, deterministic preprocessing, identical
  2,048-dimensional normalized head, and three core training objectives.
- The 80/20 class-disjoint development partition, final training on all 100
  auxiliary actions, 20 official novel actions, and exact official anchors.
- The primary query's exclusion of 40 synchronized anchor-camera mates and
  the separate exact-official query definition.
- Paired seeds, initial heads, physical P=8, K=4 batches, tuning budget,
  corruption families and severities, metrics, estimand, and claim rule.
- The immutable run and artifact provenance requirements, result-blind
  selection, one-time test opening, and prohibition on changing the study
  after observing novel-test results.
- Dataset access terms and the separate requirement for the applicable BU
  human-subjects/data-governance determination.

## Approval fields — unfilled

- Advisor decision: ____________________
- Advisor decision date and time, including timezone: ____________________
- Result-blind review confirmation and public-safe evidence reference: ____________________
- Conditions or requested changes: ____________________
- Approved amended protocol canonical SHA-256: ____________________

Private correspondence must remain outside Git and public tracker exports.
The existing protocol approval does not fill these amendment fields.

## Implementation follow-up after approval

1. Record the actual advisor decision and conditions. Confirm that the novel
   test has not been opened and no novel-test outcomes informed the amendment.
   Preserve the existing approval and every prior run or lock artifact.
2. Apply only the approved input-contract change to `configs/protocol.v1.yaml`
   and `docs/protocol/protocol-v1.md`. Update
   `DatasetConfig.expected_source_sample_count` in `src/pose_embed/config.py`,
   which currently permits only `114480`, to enforce the approved usable count.
   Bind the approved input hashes and nominal/excluded counts explicitly; do
   not weaken the count check to accept arbitrary subsets.
3. Confirm and test the existing `ntu_aggregate_inventory` validation path in
   `src/pose_embed/protocol.py`. It must verify both physical files, revalidate
   annotations, reject missing-list overlap and changed or incomplete inputs,
   and bind the exact source inventory and ordered final subsets. Retain the
   existing test seal and immutable feature-cache provenance checks.
4. Run `uv run pose-embed data generate` with the approved protocol, verified
   data root, and a fresh `--output-dir` under `POSE_EMBED_ARTIFACT_ROOT`.
   Compare the generated identities and manifest digests against the existing
   audit. Explain any difference before acceptance; never overwrite an earlier
   bundle. Run the inventory, manifest, and protocol tests, plus
   `python scripts/verify_workspace.py` and the applicable project checks.
5. Obtain the canonical amended digest from `uv run pose-embed protocol verify`
   and bind the advisor's approval to that exact digest. Preserve obsolete
   locks as historical records; use newly approved bindings for future
   artifacts. Complete evaluation-plan, final-run-set, and protocol-lock
   records only at their prescribed stages, then require
   `pose-embed protocol verify --require-locked` before any final evaluation.
6. Update the public input evidence and tracker task/gate using verified
   results and the actual approval reference. Week closure still requires
   the separate BU determination, actual time record, and all other required
   tasks and gates. This draft alone cannot authorize novel-test access,
   satisfy institutional governance, or close the week.
