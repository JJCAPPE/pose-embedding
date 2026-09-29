# Week 3 SCC execution

Execution completed September 27, 2026 EDT. Status: **all technical gates passed;
formal week closure pending**. The [compact evidence record](week-3-scc-evidence.json)
contains the verified cache identities, measurements and SHA-256 bindings.

## Scope and source

This run covers the frozen-encoder and evaluator work retained in Week 3 of
`plan/research-plan.v2.json`. Frozen 8,704-value caches are supplementary to the
v2 fine-tuned study. They do not replace its selection campaign, final training,
or independently locked evaluation.

The SCC run uses clean release
`b92e7dd88fc261c0b8585039fbe99ad67ee8b445`, based on the merged full v2 implementation
`d9b8fb4e490f0462a9e90c172e1294df33d3d8c9`. The original local working tree and
previous SCC releases are preserved. The adopted input protocol remains
`c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.
The [researcher-confirmed BU determination](../compliance/computational-research-scope.md)
was already recorded on September 24; no new confirmation was required.

## Software verification

The final local suite passed **797 tests with no skips**, including the pinned
MotionBERT and AVSL source comparisons. Locked dependency sync, workspace policy,
Ruff lint/format, shell syntax and Git whitespace checks passed. The tested tree
is byte-identical before and after rebasing these changes onto the merged release.
The full test log SHA-256 is
`37f73826dfae9de98442fedce41fcb6ffcf6f9f890c17e29a80eec782bfd6fd0`.

Week 3 commands now respect both test seals. The restriction is applied at the
parity, extraction, episode-generation and repeatability boundaries; shared
source validation remains available to fully authorized v2 final evaluation.
Regression tests distinguish those paths. A new hand-calculated fixture gives
queries different numbers of eligible positives, checks each query's AP/AP@R
denominator, and verifies equal query weighting. Historical one-shot fixtures
remain separate from the v2 multi-positive tests.

The SCC setup runner requires the explicitly selected adopted manifest bundle,
validates its protocol/source bindings before regeneration, and compares the
complete regenerated directory. Its time limit is two hours and test output
includes durations. Deterministic CUDA configuration is set before preflight
because provenance probes can initialize CUDA even in a CPU-model test.

## Preserved attempts

- Historical setup job `7749372` was killed at its 1,801-second wall limit.
  It did not produce a successful setup record.
- Setup job `7761664` was cancelled during dependency installation to use the
  final audited release. It did not start scientific extraction.
- Job `7761684` failed preflight: 668 tests passed, 86 failed and 42 errored.
  CUDA had been initialized before the deterministic cuBLAS setting. The
  corrected retry changes initialization order, not scientific settings.
  Its setup log SHA-256 is
  `8353c7646fcdfbff79ff27adc26a216f101d4f5d05e5f731690901a5343e10e8`;
  scheduler log SHA-256 is
  `ae748bbdbf172029be331c611625c1017f25dbd925177037d96af0c93d39239d`.
  No Week 3 extraction artifacts were created by that attempt.

## Completed allocated run

Job `7761714` completed setup, fresh parity, two full 95,001-row extractions in
separate processes on one NVIDIA L40S, repeatability verification, and the
development-training/gallery/query caches in that order. Setup passed at
`2026-09-28T00:09:47Z`, including **797 tests with no skips in 139.85 seconds**.
Fresh parity passed on the fixed 48-sample panel. Scheduler accounting records
`failed=0`, `exit_status=0` and **5,713 seconds** total wall time, ending at
`2026-09-27T21:40:59-04:00` (`2026-09-28T01:40:59Z`). The final observation at
`2026-09-28T01:49:27Z` confirms the extraction completion marker, all five validated
caches, the clean source release, and absence of both novel-test opening ledgers.
Setup, parity and final scheduler-log hashes are in the compact evidence record.

Raw logs remain under `setup/week3-b92e7dd/` and `logs/pose_week3.o7761714`
below `POSE_EMBED_ARTIFACT_ROOT`. Scientific outputs use the new directory
`evidence/week-03/20260928T000949Z-7761714-b92e7dd88fc2/`.
Inputs, weights, caches and full run records remain outside Git. Both novel-test
seals remained intact after execution.

## Verified auxiliary caches and resource forecast

Both clean `final_train` caches contain **95,001 × 8,704 float32 values**.
The verifier confirmed identical arrays, NPZ bytes and sample order from
sequential fresh processes (PIDs `473689` and `476024`) in job `7761714` on the
same NVIDIA L40S. Both sidecars bind the clean release, adopted inputs,
checkpoint, preprocessing, parity and deterministic CUDA environment.

All five caches passed validation, including complete provenance and their
ordered manifest identities:

| Cache | Rows | Values per row |
|---|---:|---:|
| `final-train-first.npz` | 95,001 | 8,704 |
| `final-train-second.npz` | 95,001 | 8,704 |
| `development-train.npz` | 76,013 | 8,704 |
| `development-gallery.npz` | 20 | 8,704 |
| `development-queries.npz` | 18,929 | 8,704 |

The development gallery/query caches bind the fixed episode, including its
synchronized-view exclusions. Detailed measurements and every cache, sidecar,
manifest and sample-order digest are retained in the compact evidence record.

| Measurement | First extraction | Second extraction |
|---|---:|---:|
| Recorded wall time (seconds) | 1,758.60 | 1,765.83 |
| Cache size (bytes) | 3,315,915,790 | 3,315,915,790 |
| Peak GPU allocated memory (bytes) | 3,010,839,552 | 3,010,839,552 |
| Peak GPU reserved memory (bytes; gate uses this larger peak) | 3,896,508,416 | 3,896,508,416 |
| Peak host memory (bytes) | 8,211,828,736 | 8,053,698,560 |

The conservative forecast uses the slower run, a 25% time margin and a 10%
storage margin. For all 113,945 usable source samples it projects **2,647.44
seconds (44.12 minutes)** and **4,374,851,077 bytes (4.07 GiB)** per cache.
All five report checks passed: runtime, cache storage, GPU memory, host memory
and remaining storage. The repeatability report observed 494,411,972,608
filesystem-free bytes. After all caches completed, the separate project-quota
reading gives an effective **356.93 GB remaining** (18,800 GB quota minus
18,443.07 GB used). Even treating those GB as decimal, 356.93 GB exceeds the
required 200 GiB (214.75 decimal GB) reserve.
These measurements cover Week 3 extraction only; resource approval for the
full v2 campaign remains separate.

Future runs of `scripts/extract_motionbert_week3.qsub` also capture
`pquota textconv` beside their immutable run evidence. The repeatability
verifier requires that fresh snapshot, binds its hash and time to the report,
and checks the smaller of filesystem free space and the matching project quota.
The completed job `7761714` predates this automated check; its separate
post-run project-quota observation above remains the evidence for that gate.

A later read-only SCC quota check on September 28 showed
`/projectnb/textconv` at **18,505.50 / 18,800 GB used**, or **294.50 GB
remaining**. This shared quota can change independently of this project. It
does not revise the successful, time-specific Week 3 extraction gate, but is
below the **599.27 GB encoder-and-optimizer checkpoint floor** for the complete
v2 training matrix, before most method state or retained segments; see the
[v2 storage calculation](v2-resource-floor.md). Frozen-cache timing and memory
cannot establish the cost of fine-tuning: the priority physical batch failed
on an L40S and passed its three-step profiles on an A100 80 GB, while the other
methods remain unprofiled on allocated GPUs (see the
[v2 implementation record](v2-implementation-record.md)).

The final supporting observation is preserved locally at the ignored path
`artifacts/evidence/week-03/scc-observation-7761714-20260928T014925Z.json`;
its SHA-256 is bound by the public compact evidence record. Earlier observations
and failed attempts remain preserved.

## Completion status

| Technical gate | Result | Evidence |
|---|---|---|
| 1 — repeated clean extraction | Passed | Two complete same-GPU runs; identical arrays and NPZ bytes |
| 2 — hand-calculated metrics | Passed | Historical one-shot fixtures and unequal-relevance v2 fixture; 797-test suite passed |
| 3 — complete cache provenance | Passed | All five auxiliary/development caches validated |
| 4 — measured compute/storage | Passed | All five forecast checks and final project-quota reserve passed |
| 5 — independent v2 retrieval/test seals | Passed | [Previously verified v2 implementation](v2-implementation-record.md); unequal-positive retrieval and seal regressions passed again in the 797-test suite |

Week 3 technical work is complete. Formal closure remains pending because actual
researcher minutes have not been supplied. The later hosted closures of Weeks 1
and 2 with zero recorded minutes need researcher reconciliation; see the
[handoff](weeks-1-3-handoff.md). Those records were not invented. This evidence
does not authorize or complete
the v2 selection campaign, final training or novel-test evaluation. Recheck
available quota and measure the complete backward and retrieval paths before
committing the full campaign.
