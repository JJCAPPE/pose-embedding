# Week 3 gate: real MotionBERT feature extraction

Status: **all technical gates passed in SCC job `7761714`; formal week closure
pending**. The [SCC execution record](week-3-scc-execution.md) records successful
setup, fresh GPU parity, exact repeatability, all five validated caches and
passing resource checks. The [compact evidence](week-3-scc-evidence.json) retains
their measurements and digests. The
[execution plan](../../plan/week-03-execution-plan.md) fixes the choices; the
[implementation record](week-3-implementation.md) preserves the September 24
software evidence.

The pinned Apache-2.0 checkout is available through
`scripts/fetch_upstreams.py` at MotionBERT commit
`705d3a95354db8bdb696b3492e47a3b5537174ff`. The pretrained MotionBERT
checkpoint has been verified below the ignored local data root, with
public-safe metadata in `data/manifests/motionbert-checkpoint.v1.json`. The
authorized HRNet aggregate is also present and verified, with public-safe
metadata in `data/manifests/ntu120-hrnet.v1.json`. Its 113,945 usable
annotations reconcile exactly to the nominal 114,480 captures after applying
the dataset authors' 535-item missing-skeleton list. The result-blind
[input amendment](input-contract-amendment.v1.md) is adopted at protocol SHA-256
`c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.
The researcher confirmed the applicable
[BU determination](../compliance/computational-research-scope.md) on September 24,
2026. This prerequisite is recorded as met; full-cache evidence is now verified.

## Implemented contract

1. Use the verified Week 2 manifest bundle as the source-identity contract. Its
   trusted importer hashes the complete `ntu120_hrnet.pkl` container and
   missing-skeleton list before loading, derives IDs only from
   `annotations[].frame_dir`, validates count accounting, NTU fields, duplicate
   absence, labels, pose metadata, and official anchors, and emits a normalized
   inventory plus seven metadata-only manifests. Populate the final evaluation
   plan with `kind: ntu_aggregate_inventory` and the two physical source hashes.
   Do not emit fictional per-sample files or create a replacement
   `ntu120_hrnet_oneshot.pkl`. The adopted bundle alone is not final-test
   authorization: the later protocol locks and test-opening ledger still apply.
2. Use the verified pretrained checkpoint below `POSE_EMBED_DATA_ROOT`, whose
   filename, source URLs, architecture/config ID, byte size, and SHA-256 are
   recorded in `data/manifests/motionbert-checkpoint.v1.json`. Never commit the
   weights.
3. Record the GPU model, driver, CUDA runtime, storage/job constraints and
   compatible locked PyTorch wheel. CPU tests are not GPU repeatability evidence.
4. Add a local adapter that imports the pinned checkout rather than copying it,
   instantiates the exact DSTformer architecture used by the checkpoint, loads
   weights fail-closed with complete key/shape coverage, calls `eval()`, and
   disables gradients on every encoder parameter.
5. Implement the protocol's ordered HRNet COCO17-to-MotionBERT H36M17 input
   pipeline, including the local corrected confidence conversion,
   deterministic 100-frame sampling, two-person tracking/padding, and spatial
   normalization. Do not reuse the upstream one-shot training loop because it
   evaluates novel classes during training.
6. Verify parity in named layers. Compare coordinate normalization, tracking,
   coordinate mapping, sampling/padding, spatial normalization, frozen encoder
   representations, pooled head inputs, and normalized embeddings against the
   pinned upstream path where their semantics agree. Feed an identical local
   tensor to both encoder paths when checking encoder parity. Test confidence
   separately against the protocol's hand-calculated H36M source mapping and
   minimum-source rule. The local confidence channel is intentionally corrected
   and is expected to differ from the upstream preprocessing behavior; never
   claim whole-preprocessing or confidence bit parity. Repeat extraction twice
   and require identical output. Record tolerances, device/dtype, upstream
   commit, source hashes, checkpoint hash, input-manifest hash, and ordered
   sample hash.
7. `features parity` records the fixed 48-sample panel and numerical checks.
   `features extract --backend motionbert` requires its passing hash-bound
   report on the same device/runtime and accepts only complete auxiliary
   training splits or the fixed development gallery/query episode. It writes
   deterministic float32 `[N, 8704]` unnormalized pre-head features at batch 32,
   with deterministic CUDA, no mixed precision and no TF32. Archive contents
   and complete provenance validate before the immutable approval sidecar is
   published. Partial or overwritten artifacts cannot be reused.

The development gallery is selected by the fixed lowest-hash rule, one item per
class; all synchronized views of each gallery performance are excluded from
queries. Its ordered manifest hashes are frozen before scores. Stable cosine
ranking and top-1/MRR/R@5 fixtures are implemented. The scheduler script
`scripts/extract_motionbert_week3.qsub` runs parity, two fresh complete
95,001-row auxiliary extractions on one GPU, the repeatability/resource gate,
then development-training and development-gallery/query caches.

## Exit evidence

- Pinned checkout commit and Apache notice verified.
- Checkpoint provenance/hash and strict load report recorded.
- CPU fixture tests remain green; GPU forward profile is recorded.
- Every named compatibility layer passes on authorized data; confidence passes
  the local semantic oracle and is explicitly excluded from upstream bit parity.
- Two extractions have identical artifact and sample-order hashes.
- The slower run forecasts at most 4 hours, 6 GiB per full cache, 16 GiB peak GPU
  memory and 32 GiB host memory, with twice the remaining artifact budget free.
- All development caches validate. The BU prerequisite is researcher-confirmed;
  actual researcher time remains a formal closeout input. The later hosted
  zero-minute Week 1–2 closures need reconciliation. The research checkpoint
  prompt is optional under current
  independent-research governance.
- No data, checkpoint, cache, private URL, or full run artifact is tracked.

Technical gates 1, 3 and 4 passed with the completed SCC evidence; gate 2's
hand-calculated fixtures also pass. Both novel-test opening ledgers were absent
after the run. Formal Week 3 closure remains pending prior-week closeout and
actual researcher time. These frozen caches cannot replace raw input and
backward passes in the v2 fine-tuned campaign. Novel/corrupted extraction
remains unavailable in this Week 3 backend. Later v2 selection, training and
test-opening gates remain separate.
