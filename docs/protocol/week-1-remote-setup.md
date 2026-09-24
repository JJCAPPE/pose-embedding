# Week 1 remote data and setup

Status: **technical setup verified** at `2026-09-24T15:35:26Z`.
This completes `w01-task-02`'s input inventory/checksum deliverable. It does
not decide the separate protocol or BU gates, or close the weekly record.

## Inputs and storage

The authenticated [NTU download portal](https://rose1.ntu.edu.sg/dataset/actionRecognition/)
was checked on 2026-09-24. Access remains active; the portal displays expiry
`2026 October 12 21:00` without a timezone. No authenticated download links,
credentials, or private approval correspondence are included here.

The required HRNet COCO-17 aggregate, official missing-skeleton list, pinned
one-shot definition, MotionBERT checkpoint, and provenance records are saved
on BU SCC. `POSE_EMBED_DATA_ROOT` points to the researcher's existing project
data directory; `POSE_EMBED_ARTIFACT_ROOT` points to the corresponding project
artifact directory. Both directories are owner-only (`0700`). The prior home
copies and historical artifacts were preserved. The protected data occupies
about 1.4 GiB; the original manifest bundle occupies about 54 MiB.

The [input inventory](week-1-input-inventory.md) records the exact byte counts
and SHA-256 digests. The source accounting remains **113,945 usable annotations
+ 535 official exclusions = 114,480 nominal captures**, including all 120
actions and all 20 official exemplars. The pinned public one-shot README is
also retained at `provenance/sources/NTURGB-D-README-ac2ebc87.md` below the data
root (14,328 bytes; SHA-256
`1968e07f83bd7e9ea2ac6f9797bbfe880e59828b7b0f1644b3e5736ea68acc33`).

No raw RGB/depth/infrared or Kinect 25-joint 3D archive is required by the
locked HRNet study. Downloading those modalities would not restore the 535
official exclusions or satisfy the different 17-joint 2D input contract.

## Reusable remote setup

An `environment.sh` beside the SCC checkout sets the data/artifact roots,
the managed Python installation directory, and the installed `uv` path.
After sourcing it and entering the checkout, submit verification with:

```bash
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/verify_scc_setup.qsub
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/profile_motionbert_gpu.qsub
```

Run the setup verification to successful completion before relying on a new
environment. It installs the locked Python 3.11 dependency graph, checks the
workspace and pinned MotionBERT source, runs Ruff and the full test suite,
checks the protected input checksums, and regenerates the complete manifest
bundle into a new job-specific artifact directory. Every regenerated file is
compared byte-for-byte with `manifests/ntu120-v1-release-20260916`; historical
bundles are never overwritten. Tests use isolated synthetic fixtures rather
than the live data/artifact roots. Dependency caching uses node-local temporary
storage, not the limited home quota.

The GPU script performs only dense synthetic-input frozen-encoder profiling.
It is not a real-data extraction, training, retrieval evaluation, or Week 3
adapter-parity check.

## Selected setup verification

Grid Engine job `7720715` completed successfully from clean commit
`56da0d8373bfecfcbfb25665a0c46863efc9c18a`. It verified:

- Python 3.11.15 and the locked dependency environment with `uv 0.11.27`.
- The workspace policy, pinned MotionBERT checkout, unchanged protocol hash,
  Ruff lint/format checks, and **all 108 Python tests**.
- Matching SHA-256 checks for the aggregate, missing list, and checkpoint.
- Structural validation of all 113,945 usable annotations, then regeneration
  of the source inventory, seven split manifests, audit, and manifest-set
  metadata. All ten files match the release bundle byte-for-byte.
- Absence of the novel-test opening ledger. No final evaluation ran.

The new immutable bundle is `manifests/scc-verification-7720715` under the
artifact root. Its `manifest-set.json` SHA-256 is
`e4fd9f4b144b66053af61868ab1cb1e70ec9d6a5b17077122496c36b16500540`;
the [manifest audit](ntu-manifest-audit.v1.md) lists the unchanged split digests.
The verification script SHA-256 is
`8c91b989b0994fa4e36075d75b74871546bc9c83563552ee132cadfa0069636e`.
Its full log remains at `logs/pose_setup_verify.o7720715` outside Git,
SHA-256 `fb23d198e6f6761a3105c2673b08d50842d7a822556c10ad730f5b54ef09520e`.
Home usage was 8.50/10.0 GB (11.0 GB hard limit); the shared project allocation
reported 18,381.27/18,800 GB. Those are usage observations, not reserved future
capacity; new data and generated artifacts use project storage.

The first executed check (`7720663`) preserved 107 passing tests and one
failure because a missing-lock unit test inherited the real artifact root.
The corrected script unsets the live roots only for the test process; the
successful rerun still checks the real inputs and manifests. The CPU queue
reported an old-driver warning during a CUDA-availability probe; the tests
ran on CPU, and the separate assigned-GPU job below verifies CUDA operation.
An earlier queued job (`7720651`) was cancelled before execution when the
storage roots were moved to the existing project allocation. These logs and
historical artifacts were retained.

## Fresh GPU verification

Job `7720685` completed a fresh profile at `2026-09-24T15:33:40.939693Z`
using the project-storage checkpoint and clean commit
`56da0d8373bfecfcbfb25665a0c46863efc9c18a`. The scheduler assigned one NVIDIA
L40S (44.421 GiB), driver `610.57.04`, with PyTorch `2.9.1+cu128`, CUDA 12.8,
and Python 3.11.15. All required environment evidence commands succeeded.

| Physical batch | Result | Peak allocated | Peak reserved | Median forward |
| ---: | --- | ---: | ---: | ---: |
| 32 | success | 2.572 GiB | 2.855 GiB | 516.326 ms |
| 64 | success | 4.977 GiB | 5.514 GiB | 1,047.984 ms |

Physical batch **32 remains selected** until all core objectives are profiled
in Week 4. The new profile supplements, rather than replaces, the original
[A40 profile](week-1-gpu-profile.md). Its immutable raw artifact is
`profiles/motionbert-gpu-7720685-20260924T153254Z.json` under the artifact root,
SHA-256 `c287a507a184c256a3a0f9dd89e3258ce888d4d3cff9e1f4e78c48c044ee0ead`.

## Remaining closure decisions

Technical input verification, protocol decisions, and institutional requirements are separate.
The [input-contract amendment draft](input-contract-amendment-draft.md) is
prepared but **not adopted**. The protocol still requires 114,480 source rows
and therefore needs a documented result-blind amendment accepting the verified
usable aggregate and physical-source binding. The setup evidence above binds
the original protocol hash. The subsequent governance-only revision is recorded
in [Independent research governance](independent-research.md); it removes advisor
requirements without adopting the input-contract amendment.

Week closure still requires:

1. The documented input-contract amendment (`w01-gate-02`).
2. The applicable BU governance determination (`w01-gate-04`), subsequently
   confirmed by the researcher on 2026-09-24 without an attachment. See the
   [confirmation record](../compliance/computational-research-scope.md).
3. The researcher's actual Week 1 minutes, not an estimate inferred from planned
   hours, elapsed automation time, or GPU runtime.

To enter time in the owner interface: **Manage → Week 1 → Week details →
Actual minutes → Save week**. Convert hours to minutes (for example, 2.5 hours
is 150 minutes). No time or external approval has been invented, and the
novel-test seal has not been opened.
