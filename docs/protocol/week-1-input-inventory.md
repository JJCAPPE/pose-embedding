# Week 1 input inventory

Status: **technical input verification complete; protocol acceptance pending**.
The initial verification at `2026-09-13T02:07:49Z` was reproduced on the GPU
host at `2026-09-24T15:35:26Z`; see the [remote setup evidence](week-1-remote-setup.md).
The licensed pose aggregate is present, checksummed, readable, and structurally
valid. The inventory/checksum deliverable closes `w01-task-02`, but the separate
`w01-gate-02` remains pending: the aggregate contains 113,945 usable skeleton
samples after the official 535-item exclusion, while protocol v1 requires a
114,480-row inventory backed by declared per-sample files. Technical verification
does not authorize that protocol amendment.

All local paths below are relative to `POSE_EMBED_DATA_ROOT`. Protected files
remain outside Git; this repository contains only public-safe provenance and
checksums.

The primary-source audit supporting the acquisition decision is recorded in
[`ntu-input-source-research.md`](ntu-input-source-research.md).

## Verified inputs

| Input | Public source | Local path | Bytes | SHA-256 | Readability result |
|---|---|---|---:|---|---|
| NTU RGB+D 120 HRNet poses | [MotionBERT action-data instructions](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/docs/action.md#data); [pinned OpenMMLab instructions](https://github.com/open-mmlab/mmaction2/blob/a5a167dff2399e2d182a60332325f9c0d4663517/tools/data/skeleton/README.md#prepare-annotations); [current OpenMMLab mirror](https://download.openmmlab.com/mmaction/v1.0/skeleton/data/ntu120_2d.pkl) | `ntu120_hrnet.pkl` | 1,238,461,428 | `aaf1f928b4629fa9a0850528d43fdd8d920532805d16672bfdda78085b649df8` | The trusted pickle loaded in 4.3 seconds. Its `split` and `annotations` structures contain 113,945 unique canonical IDs spanning A001-A120, no label/ID mismatch, finite COCO-17 coordinates and confidence, and all 20 official exemplars. The local MD5 is `31c0efd891f18b942403de3376cee000`, matching the server ETag and `Content-MD5`. |
| Official NTU RGB+D 120 missing-skeleton list | [NTURGB-D list at locked commit](https://github.com/shahroudy/NTURGB-D/blob/ac2ebc87e6e9777ea6bac67e65e53b325b903f74/Matlab/NTU_RGBD120_samples_with_missing_skeletons.txt) | `provenance/sources/NTU_RGBD120_samples_with_missing_skeletons.txt` | 11,451 | `ab14fe64e89be63d2b08141713fcc31f6ebc7b01955009c3585d8d3367e0facc` | The source contains 535 unique canonical IDs. None occurs in the HRNet aggregate, and the 535-item exclusion exactly explains the difference between 114,480 nominal captures and 113,945 usable annotations. |
| Official NTU RGB+D 120 one-shot protocol definition | [NTURGB-D README at locked commit](https://github.com/shahroudy/NTURGB-D/blob/ac2ebc87e6e9777ea6bac67e65e53b325b903f74/README.md#evaluation-protocol-of-one-shot-action-recognition-on-ntu-rgbd-120) | Not applicable (public source) | 14,328 | `1968e07f83bd7e9ea2ac6f9797bbfe880e59828b7b0f1644b3e5736ea68acc33` | UTF-8 source parsed; its 20 exemplar IDs are unique and match `configs/protocol.v1.yaml` in exact order. |
| Generic pretrained MotionBERT | [Pinned model-zoo entry](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/README.md#model-zoo); [immutable author mirror](https://huggingface.co/walterzhu/MotionBERT/blob/370a9196aa3c89198b134c82476143b01c0fb32c/checkpoint/pretrain/MB_release/latest_epoch.bin) | `checkpoints/MB_release/latest_epoch.bin` | 169,958,969 | `02a9ee017e5c9d688b5dd41e0055bddb75b6eee7f5eed326a8cdc6e5bf08eaf8` | `torch.load(..., weights_only=True)` parsed 260 tensors. After removing the upstream `module.` prefix, strict loading into the pinned full MotionBERT DSTformer reported no missing or unexpected keys; a CPU smoke input produced a finite `float32` representation with shape `[1, 100, 17, 512]`. |

The checkpoint uses `configs/pretrain/MB_pretrain.yaml` at MotionBERT commit
`705d3a95354db8bdb696b3492e47a3b5537174ff`; that config's SHA-256 is
`bc58dfbe5b00424afb6542217c820cca3817f2a859fe84667ef678a08a6b58f8`.
The metadata-only checkpoint record is
`data/manifests/motionbert-checkpoint.v1.json`.

The locked one-shot partition does not require MotionBERT's unavailable
`ntu120_hrnet_oneshot.pkl`. The NTU source above defines the 20 novel classes,
the one exemplar for each class, and all remaining novel-class samples as
queries. `build_manifest_records` derives those memberships from the full
aggregate's canonical `frame_dir` IDs without writing a replacement pose
dataset. The old OneDrive container remains useful only for optional
byte-for-byte reproduction of MotionBERT's packaging.

## HRNet source resolution

MotionBERT's pinned instructions name the older OpenMMLab object
[`ntu120_hrnet.pkl`](https://download.openmmlab.com/mmaction/pyskl/data/nturgbd/ntu120_hrnet.pkl).
The pinned current [MMAction2 skeleton instructions](https://github.com/open-mmlab/mmaction2/blob/a5a167dff2399e2d182a60332325f9c0d4663517/tools/data/skeleton/README.md#prepare-annotations)
publish the same dataset as
[`ntu120_2d.pkl`](https://download.openmmlab.com/mmaction/v1.0/skeleton/data/ntu120_2d.pkl).
At the verification time above, both endpoints returned the same
`Content-Length` (1,238,461,428), `Content-MD5`/ETag
(`31c0efd891f18b942403de3376cee000`), and OSS CRC64
(`1947771371206224206`). The downloaded current-mirror payload matches those
fields and now has the independently computed local SHA-256 recorded above.

The two Google Drive archives linked by the NTU authors are not substitutes.
They resolve to `nturgbd_skeletons_s001_to_s017.zip` (6,181,024,200 bytes) and
`nturgbd_skeletons_s018_to_s032.zip` (4,780,938,300 bytes). They hold the NTU
Kinect 25-joint 3D skeleton modality; this protocol requires the OpenMMLab
HRNet-W32 17-joint COCO 2D coordinates and confidence scores.

## Protocol input-contract discrepancy

The dataset authors state that 535 captured NTU RGB+D 120 samples have missing
or incomplete skeleton data and should be ignored for skeleton-based analysis.
The locked source list contains exactly 535 unique IDs; none occurs in the
downloaded HRNet aggregate. The aggregate's 113,945 unique annotations plus
those 535 exclusions exactly reproduce the dataset's nominal 114,480 captures.
All 120 action labels and all 20 official one-shot exemplars remain present.

This evidence rules out truncation, but it does not authorize silently changing
the hash-bound protocol. `configs/protocol.v1.yaml` and
`docs/protocol/protocol-v1.md` currently require a 114,480-row canonical source
inventory and explicitly require an amendment when an authorized complete
inventory differs. Before the novel test can be opened, record a result-blind
documented amendment that binds both the 113,945 usable annotations plus
the missing-list digest above and verification of those two hash-pinned physical
inputs in place of 114,480 declared per-sample files, or records another
documented resolution.

## Completed technical checks

1. [x] Confirm approval from ROSE Lab and authenticated access to the current
   NTU RGB+D/120 download portal. The private approval record remains outside
   Git; the portal displayed an expiry of `2026 October 12 21:00` without a
   timezone label.
2. [x] Download the full HRNet aggregate from the current byte-matched
   OpenMMLab endpoint into the ignored data root, name it `ntu120_hrnet.pkl`,
   and verify its byte count, MD5, and local SHA-256 before loading it.
3. [x] Parse every available annotation; verify the top-level structures,
   canonical identifiers, zero-based labels, ranges, duplicate absence, finite
   pose arrays, and exact 20 official anchors; reconcile the 535 absent records
   to the locked dataset-author exclusion list.
4. [x] Preserve the required inputs and provenance on the GPU host, recheck
   physical-file SHA-256 digests, and regenerate the entire manifest bundle
   byte-for-byte under a fresh artifact path. The remote workspace verifier,
   Ruff checks, and all 108 tests passed; licensed inputs remain outside Git.

## Pending protocol acceptance

1. [ ] Record the result-blind input-contract resolution
   described above before opening the novel test. The
   [prepared amendment](input-contract-amendment-draft.md) is a draft that has not been adopted.
2. [ ] Apply only the documented amendment, reverify the bound inputs and protocol
   digest, and update `w01-gate-02` with the actual decision evidence. Do not
   overwrite historical inputs or artifacts, or infer protocol adoption from task completion.
