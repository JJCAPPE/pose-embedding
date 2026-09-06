# Week 1 gate: real MotionBERT feature extraction

Status: **blocked deliberately**. The repository can exercise the complete
artifact plumbing with synthetic fixtures, but it cannot yet create or consume
scientific MotionBERT feature caches. `validate_feature_artifact` rejects every
`backend: motionbert` sidecar until this gate is implemented and verified.

The pinned Apache-2.0 checkout is available through
`scripts/fetch_upstreams.py` at MotionBERT commit
`705d3a95354db8bdb696b3492e47a3b5537174ff`. No pretrained MotionBERT checkpoint
is present in the workspace, and no authorized NTU HRNet sample is available,
so numerical encoder parity cannot honestly be established yet.

## Smallest remaining implementation

1. Put the authorized `ntu120_hrnet.pkl` and `ntu120_hrnet_oneshot.pkl` below
   `POSE_EMBED_DATA_ROOT`. Implement a trusted importer that hashes each complete
   container before loading it, derives canonical sample IDs only from
   `annotations[].frame_dir`, validates the exact source count, NTU field ranges,
   duplicate IDs, zero-based action labels, and the official anchors, then emits
   canonicalized per-sample artifacts and a metadata-only inventory. The current
   generic `data verify --check-files` command does not inspect aggregate pickle
   entries and must not be cited as aggregate verification.
2. Put the authorized pretrained checkpoint below `POSE_EMBED_DATA_ROOT` and add
   only its filename, source URL, expected architecture/config ID, byte size,
   and SHA-256 to a metadata-only manifest. Never commit the weights.
3. Record the GPU model, driver, CUDA runtime, storage/job constraints, and then
   lock the compatible PyTorch wheel. The current CPU lock is not evidence of
   GPU compatibility.
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
7. Add `features extract --backend motionbert` only after those parity tests
   pass. Its sidecar must set `scientific_use_allowed: true`, identify the
   frozen-encoder cache for training or the exact trained objective/seed for
   retrieval embeddings, and pass the existing sidecar verifier. Remove the
   hard failure only in the same reviewed change.

## Exit evidence

- Pinned checkout commit and Apache notice verified.
- Checkpoint provenance/hash and strict load report recorded.
- CPU fixture tests remain green; GPU forward profile is recorded.
- Every named compatibility layer passes on authorized data; confidence passes
  the local semantic oracle and is explicitly excluded from upstream bit parity.
- Two extractions have identical artifact and sample-order hashes.
- No data, checkpoint, cache, private URL, or full run artifact is tracked.

Until all seven steps and exit evidence exist, the fixture backend is useful only
for plumbing tests and final evaluation must remain unavailable.
