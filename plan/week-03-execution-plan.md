# Week 3 — frozen MotionBERT and retrieval

Implementation plan recorded on 2026-09-24 for September 28–October 4.
The input-contract amendment is adopted at protocol SHA-256
`c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.
Current independent-research governance replaces historical advisor sign-off
with researcher decisions. The recorded BU determination and actual research
minutes remain separate requirements; do not infer either from code completion.

## Ordered work

1. Verify the adopted protocol, complete Week 2 bundle, physical input hashes,
   pinned checkpoint and upstream checkout, clean code, and absent test-opening
   ledger. Scientific extraction stops when a prerequisite is unresolved.
2. Share the strict frozen MotionBERT loader and action-head pooling. Implement
   camera normalization, joint tracking with the same confidence permutation,
   corrected COCO17-to-H36M17 coordinates/confidence, uniform 100-frame sampling,
   second-person padding, and the locked spatial normalization in that order.
3. Freeze a 48-sample auxiliary parity panel: eight per combination of one/two
   pose tracks and fewer than/exactly/more than 100 frames. Select by ascending
   SHA-256 of `protocol-v1|week-3-parity-v1|<sample_id>`, then restore source order.
   Compare discrete operations exactly, preprocessing at absolute/relative
   tolerance `1e-6`, and encoder/pooling/head at absolute `1e-6`, relative `1e-5`.
   Confidence uses its own hand-calculated minimum-source oracle. Encoder and
   spatial parity receive identical local inputs wherever corrected confidence
   affects the upstream path. Preserve native upstream arithmetic in intermediate
   stages; the final encoder tensor is float32.
4. Add `features parity` and `features extract --backend motionbert`. Cache
   unnormalized pooled `float32 [N, 8704]` features in deterministic NPZ files.
   Require passing parity and bind data, manifest bundle, selected manifest,
   ordered samples, local code, upstream, checkpoint, protocol, environment,
   and artifact hashes. Use immutable outputs and reject incomplete caches.
5. Derive a clean validation gallery with one sample per class, selected by the
   lowest SHA-256 of `protocol-v1|dev-anchor-v1|<sample_id>`. Retain source order;
   exclude every synchronized view of each gallery performance from queries.
   Record parent and derived manifest hashes before computing any scores.
   Keep stable cosine ranking; exact ties follow gallery order. Reject zero
   vectors, duplicate query IDs, nonfinite values and malformed inputs. Verify
   correct ranks `[1, 2, 6]`: top-1 `1/3`, MRR `5/9`, R@5 `2/3`.
6. Run two complete 95,001-row final-training extractions as fresh processes on
   one scheduler-assigned GPU. Use batch 32, float32, deterministic algorithms,
   `CUBLAS_WORKSPACE_CONFIG=:4096:8`, cuDNN benchmarking off, and TF32 off.
   Require identical feature bytes, NPZ hashes, and ordered sample hashes.
   Preserve both outputs, then create development-training and validation
   gallery/query caches. Record stage times, peak GPU/host memory, storage,
   software versions, and all hashes.
7. Forecast a 113,945-row pass from the slower complete run with a 25% time
   margin and a 10% storage margin. Require at most 4 hours, 6 GiB per complete
   clean cache, 16 GiB peak GPU memory (the larger of allocated/reserved),
   32 GiB host memory, and twice a conservative 100 GiB remaining artifact
   budget free. This 200 GiB reserve covers retained caches, nine heads, their
   retrieval embeddings and run evidence; it is a reservation, not measured
   storage consumption. Run workspace verification, locked dependency sync, Ruff and
   the full Python tests. Publish compact evidence, update only supported
   Week 3 gates, and record actual researcher time/review before closure.

## Boundaries

Raw evidence and caches live under `POSE_EMBED_ARTIFACT_ROOT`; licensed source
files and checkpoints live under `POSE_EMBED_DATA_ROOT`. The 48 samples serve
parity only; repeatability requires the full auxiliary set. Training objectives
belong to Week 4, real corruptions to Week 5. Novel extraction and evaluation
remain sealed until their later protocol gates are satisfied.

## Acceptance

- Strict checkpoint loading, frozen/eval encoder and named parity layers pass.
- Two full extractions are byte-identical and include complete provenance.
- Hand-calculated metric and leakage/invalid-input tests pass.
- Altered or missing source, manifest, code, parity, checkpoint or cache fails.
- Measured time, memory and storage meet the declared forecast limits.
- Full evidence remains outside Git and public summaries state remaining blockers.
