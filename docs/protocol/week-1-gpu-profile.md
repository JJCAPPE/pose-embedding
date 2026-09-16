# Week 1 GPU and scheduler profile

Status: **complete** at `2026-09-16T16:41:15.368855+00:00`.

This record closes `w01-task-03` and supports `w01-gate-03`. The selected
immutable raw profile remains outside Git at
`$POSE_EMBED_ARTIFACT_ROOT/profiles/motionbert-gpu-7596065-20260916T164015Z.json`
(SHA-256
`e9205f6059eb4655222928c58f81c3b3cc72a5694524e8a5fb316c318a57db2c`).

## Scope

- Protocol: `protocol-v1`, SHA-256
  `12cf4d9a322f5bd5ea76fb2d9ffc070a6a2681fe8474a05cff1f62b6e43368e2`.
- Scope: dense synthetic-input compute and memory profiling of the frozen
  encoder only.
- This is not preprocessing, adapter-parity, feature-extraction determinism,
  training-memory, or scientific-result evidence.
- No NTU data, novel-test loader, participant information, or private
  correspondence was accessed.

## Model and input contract

- MotionBERT upstream commit:
  `705d3a95354db8bdb696b3492e47a3b5537174ff`.
- Checkpoint: 169,958,969 bytes, SHA-256
  `02a9ee017e5c9d688b5dd41e0055bddb75b6eee7f5eed326a8cdc6e5bf08eaf8`.
- Model: 42,466,317 parameters, 260 strict-loaded state-dict entries,
  evaluation mode, and zero trainable parameters.
- Input: protocol-shaped `float32 [B, 2, 100, 17, 3]`; the people dimension is
  flattened to an encoder batch of `2B`.
- Expected and observed representation: `float32 [2B, 100, 17, 512]` with
  finite values.
- Each batch used three warmups and ten measured forwards. CUDA events measured
  forward device time only, excluding input preprocessing and I/O.

## Device and software

| Field | Observed value |
|---|---|
| Compute service | Boston University Shared Computing Cluster |
| Scheduler / queue | Grid Engine / `ece` |
| GPU | NVIDIA A40 |
| Total GPU memory | 47,696,969,728 bytes (44.421 GiB) |
| Compute capability | 8.6 |
| Scheduler-visible GPUs | Exactly one (`CUDA_VISIBLE_DEVICES=0`) |
| NVIDIA driver | 610.57.04 |
| Python | 3.11.15 |
| PyTorch | 2.9.1+cu128 |
| PyTorch CUDA runtime | 12.8 |
| cuDNN | 9.10.2 |

## Batch profile

| Physical batch | Encoder batch | Status | Peak allocated | Peak reserved | Median forward | Throughput |
|---:|---:|---|---:|---:|---:|---:|
| 32 | 64 | success | 2,761,666,560 bytes (2.572 GiB) | 3,066,036,224 bytes (2.855 GiB) | 842.164 ms | 37.997 samples/s |
| 64 | 128 | success | 5,343,896,576 bytes (4.977 GiB) | 5,920,260,096 bytes (5.514 GiB) | 1,685.400 ms | 37.973 samples/s |

The full profiling window was 36.265 seconds. Peak values are PyTorch CUDA
allocator measurements captured before output validation, not whole-node or
process memory. The raw artifact preserves all ten timings for each batch.

## Scheduler, quota, and limits

- Selected Grid Engine job: `7596065`; request: one GPU, four CPU slots,
  30-minute wall time, compute capability at least 7.0, at least 16 GiB GPU
  memory, and 8 GiB memory per CPU slot.
- Every required driver, scheduler, queue, quota, and job-limit evidence command
  succeeded; `evidence.complete` is `true` and `failed_commands` is empty.
- Live resource-quota-set evidence limited a user to two shared GPUs and, on
  the eligible high-end queues, 16 concurrent slots. The global configuration
  reported `max_u_jobs=10000`; the scheduler-specific `maxujobs` value was `0`.
- BU documents a 48-hour maximum wall time for shared GPU jobs. This job asked
  for 30 minutes and occupied one assigned GPU only.
- Home usage at capture was 7.28965 GB against a 10 GB quota and 11 GB hard
  limit. The two available group allocations were at 186.79/200 GiB and
  18,283.65/18,800 GiB, so this profile deliberately used the private home
  workspace and no group project storage.

The operational choices follow BU's official guidance for
[GPU computing](https://www.bu.edu/tech/support/research/software-and-programming/gpu-computing/),
[batch-job submission](https://www.bu.edu/tech/support/research/system-usage/running-jobs/submitting-jobs/),
and [login-node/process limits](https://www.bu.edu/tech/support/research/system-usage/running-jobs/process-reaper/):
GPU work ran only through Grid Engine, the scheduler selected the device, and
heavy dependency installation ran in a CPU batch job rather than on the login
node.

## Physical batch-size decision

Retain physical batch size **32**.

Both encoder-only forwards fit, so physical batch 32 is feasible and the Week 1
gate is supported. Protocol v1 permits adopting batch 64 only if every core
objective fits during the Week 4 method-level profile. This encoder-only result
does not authorize that change, and gradient accumulation would not establish
physical contextual-batch equivalence.

## Reproducibility and completion log

- Clean Git commit: `e302f9c046247c5c43d78832caea3831c3b539a6`;
  `git_dirty=false` in the selected artifact.
- Profiler SHA-256:
  `ade27941aedb239e2b228c8862caea8fd974fa3c87fd0d86d5237ef1cc605890`.
- Grid Engine script SHA-256:
  `e896c8aea3544abd50f9bc4d502a753f857b66088292e584781c062ce7e318ad`.
- MotionBERT implementation SHA-256:
  `0896b29872b10f55be8902ceceacb9febe7876fa2065d5f9dd670fbb902f2f47`.
- MotionBERT config SHA-256:
  `bc58dfbe5b00424afb6542217c820cca3817f2a859fe84667ef678a08a6b58f8`.
- Provisioning used `uv 0.11.27` with the locked dependency graph. Corrected
  setup job `7596015` exited successfully after the workspace verifier, Ruff
  lint, Ruff format check, and all 108 tests passed. The initial setup attempt
  `7595995` had already passed the same checks but then exited on an incorrect
  reporting-only upstream path; its log was preserved and the corrected job
  was rerun to completion.
- The first GPU attempt, `7596038`, also completed successfully and is preserved
  as raw artifact SHA-256
  `16d782d7ac1e8f2fb9810ef504714a7835e35d0561ccda23a5a4c19cd6015b91`.
  It was superseded because it truthfully recorded `git_dirty=true` for the
  reviewed file overlay. Job `7596065` reran the identical profiler from the
  clean commit and is the evidence selected above.
- Local verification of the clean profiler commit also passed the workspace
  verifier, Ruff lint, Ruff format check, all 108 tests, shell syntax, and
  `git diff --check`.

Raw JSON, full scheduler output, logs, the checkpoint, the environment, and
caches remain outside Git. This file contains only the compact public-safe
completion evidence.
