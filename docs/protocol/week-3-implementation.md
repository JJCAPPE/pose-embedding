# Week 3 implementation record

Recorded 2026-09-24. Status: **software verified; real GPU gates pending**.
This is not a scientific extraction result and does not close Week 3.

## Implemented

- Shared strict MotionBERT loader, frozen/evaluation-mode encoder, attributed
  preprocessing adapter and shared action-head pooling.
- Fixed 48-sample parity selection and independent upstream comparisons for
  each compatible layer, plus hand-calculated corrected-confidence checks.
- Clean float32, batch-32, deterministic `[N, 8704]` pre-head NPZ extraction.
  Source, complete manifests, order, code, dependency lock, checkpoint, parity
  and archive hashes are bound by immutable sidecars. Final validation happens
  before sidecar publication; partial and incompatible caches fail closed.
- Result-blind development gallery/query manifests; synchronized camera views
  are excluded from queries. Cosine ties retain gallery order. Zero vectors,
  duplicate IDs, nonfinite values and missing relevant classes are rejected.
- Full 95,001-row two-process repeatability verifier, resource forecast and
  `scripts/extract_motionbert_week3.qsub` scheduler runner. It creates the two
  full auxiliary caches before development-training/gallery/query caches.

The complete choices and sequence are saved in
[the execution plan](../../plan/week-03-execution-plan.md).

## Choices made before results

- Use the full 95,001-row auxiliary split for repeatability; the 48-row panel is
  only for numerical parity. Select panel and gallery by fixed hashes and keep
  source order. No validation scores were viewed.
- Preserve upstream arithmetic in intermediate preprocessing, then cast the
  encoder input to float32. Correct confidence with the minimum-source rule;
  do not claim upstream confidence parity.
- Cache the 8,704-value vector before projection/normalization. Training the
  2,048-value retrieval head remains Week 4 work.
- Require exact repeated arrays and NPZ bytes on the same GPU in two distinct
  processes, with deterministic algorithms, no mixed precision and no TF32.
- Forecast from the slower run with 25% time and 10% storage margins. Reserve
  100 GiB for remaining artifacts and require 200 GiB free. This is a conservative
  reservation, not a measurement. Gate GPU memory on the larger of PyTorch
  allocated/reserved peaks; record host peak RSS including cache verification.
- Add only `easydict==1.13` to the locked dependencies because the pinned
  upstream parity oracle imports it. Its dependency notice is recorded.

## Verification evidence

Local checks on the uncommitted implementation based on
`c60c0fe40b6c7d09686079167a68c939eeb24aea`:

| Check | Result |
|---|---|
| `python scripts/verify_workspace.py` | Passed |
| `uv sync --locked --group dev` | Passed |
| Ruff lint and format check | Passed, 67 Python files |
| `uv run pytest -ra` | 322 passed, 30.88 seconds |
| Tracker lint and typecheck | Passed |
| Tracker unit tests | 15 passed |
| Tracker production build | Passed |
| Pinned MotionBERT checkout check | Passed |
| Protocol verification | Valid adopted hash; later final-test lock absent |
| Scheduler shell syntax and `git diff --check` | Passed |

The retrieval fixture with ranks `[1, 2, 6]` gives top-1 `1/3`, MRR `5/9`,
and R@5 `2/3`. Tests also exercise fixed episode rederivation, synthetic
extraction round trips, immutable failures and rejection of changed provenance.
The initial tracker test correctly noticed the newly completed task/gate;
its expected seed-plan counters were updated and all 15 tests then passed.

The raw local check logs remain Git-ignored at
`artifacts/evidence/week-03/local-checks-kwkIRn/`. Selected SHA-256 values:

- MotionBERT code bundle:
  `6be742e98d69320ed8a9e8367996b002effd1ca83948c2fe58ccb406939ccf1f`.
- `uv.lock`:
  `11ced81a29e438939a4e489835fd93ddddcd53e29fb0896212ea6a276e24bc3e`.
- `pytest.log`:
  `bb7b0042a755978e8d4cbed25aa9e58e7d562898093b067ef9467affa9bb81d0`.
- `tracker-tests-final.log`:
  `0177c17668459b6ad3c9d26cf5110d87c751c37189036b270d7f1711600e1316`.
- `tracker-build.log`:
  `254a14cb2285f99baabd2dafb76565badf259e4999bc657a5a31b5a7023260dd`.

The restored SSH session allowed read-only verification of the adopted remote
metadata: 113,945 total rows, 95,001 auxiliary rows, and at least eight samples
in every parity stratum. The novel-test opening ledger was absent. A real remote
runtime check exposed the valid `torch` runtime/package distinction
(`2.9.1+cu128` versus `2.9.1`); the validator now handles it with a regression
test while retaining exact runtime/CUDA binding. No scientific GPU job was run.

## Gate decisions and remaining work

| Gate | Decision | Remaining evidence |
|---|---|---|
| 1 — repeated clean extraction | Pending | Two complete real same-GPU extractions |
| 2 — hand-calculated metrics | Met | Fixture evidence above |
| 3 — complete cache provenance | Pending | Validate all real final/development caches |
| 4 — measured compute/storage | Pending | Slower-run time, memory and storage forecast |

At the time of this implementation record, the BU determination was pending
and scientific parity/extraction had not started. The researcher subsequently
confirmed the [BU determination](../compliance/computational-research-scope.md)
on September 24. The v2 scope amendment now prioritizes the paired development
pilot. For any extraction, use a clean committed checkout and locked GPU environment,
and submit the provided job with scheduler logs outside the repository as
shown in the README. Keep every output and failure report outside Git.

Actual researcher minutes and the researcher checkpoint response have not been
provided and were not invented. Current independent-research governance does
not require an advisor response. Head training, corruption runs and novel-test
evaluation remain outside this implementation. Only the local plan was updated;
no hosted tracker, deployment or database was changed.
