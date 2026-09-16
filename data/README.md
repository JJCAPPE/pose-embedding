# Data boundary

NTU RGB+D 120 data, MotionBERT checkpoints, extracted features, trained heads,
and full run outputs must not be committed to this repository.

Set two absolute paths before running a real experiment:

```sh
export POSE_EMBED_DATA_ROOT=/absolute/path/to/authorized/ntu120
export POSE_EMBED_ARTIFACT_ROOT=/absolute/path/to/pose-embed-artifacts
```

The data root should contain only files obtained under the applicable dataset
terms. The artifact root holds caches, checkpoints, logs, and reports. Commands
record hashes and paths in run manifests; they never copy licensed source data
into Git.

The canonical licensed pose input is the pinned `ntu120_hrnet.pkl` aggregate
described by the upstream MotionBERT action documentation. The official
one-shot partition is public metadata: derive it in memory from the locked NTU
class and exemplar IDs in `configs/protocol.v1.yaml`. MotionBERT's unavailable
`ntu120_hrnet_oneshot.pkl` is a convenience container, not an additional source
of poses required by this study. Do not create or redistribute a replacement
pose pickle.

`pose-embed data generate` is the trusted aggregate importer. It verifies the
container and official missing-skeleton hashes before unpickling, derives IDs
from `annotations[].frame_dir`, validates counts/ranges/duplicates/labels and
pose metadata, proves the official anchor and query partitions, and writes one
normalized source inventory plus seven immutable split manifests. Do not
manufacture 113,945 repeated per-row hashes for one pickle. The older `data
verify --check-files` path remains available only for genuinely per-sample
files whose filenames are canonical NTU IDs.

Expected inputs for the fixture backend are documented by
`pose-embed features extract --help`. Real MotionBERT extraction is deliberately
not presented as implemented until the authorized dataset aggregate, verified
official split definition, checkpoint, GPU runtime, and numerical parity test
are available.
See `docs/protocol/motionbert-adapter-gate.md` for the exact Week 1 unblock
checklist.

Each generated `.npz` must travel with its sibling `.npz.manifest.json`; missing
or mismatched sidecars fail closed. A sidecar records its role and split, exact
sample order, tensor shape/dtype, protocol and preprocessing hashes, upstream
and checkpoint/projection hashes, and the artifact hash. Synthetic fixture
sidecars are never valid scientific evidence.

Version-controlled files under `data/manifests/` are schemas, empty placeholders,
or small metadata-only manifests. They must not contain pose coordinates or
private storage URLs.
