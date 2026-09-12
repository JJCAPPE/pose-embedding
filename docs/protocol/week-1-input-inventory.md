# Week 1 input inventory

Status: **partially verified** at `2026-09-12T00:44:48Z`. This record does not
close `w01-task-02` or meet `w01-gate-02` until the licensed aggregate pose file
is present and checked.

All local paths below are relative to `POSE_EMBED_DATA_ROOT`. Protected files
remain outside Git; this repository contains only public-safe provenance and
checksums.

The primary-source audit supporting the acquisition decision is recorded in
[`ntu-input-source-research.md`](ntu-input-source-research.md).

## Verified inputs

| Input | Public source | Local path | Bytes | SHA-256 | Readability result |
|---|---|---|---:|---|---|
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
(`1947771371206224206`). These independent server fields are strong evidence
that the current path is a renamed mirror, but they do not replace the required
local SHA-256 after authorized download.

The two Google Drive archives linked by the NTU authors are not substitutes.
They resolve to `nturgbd_skeletons_s001_to_s017.zip` (6,181,024,200 bytes) and
`nturgbd_skeletons_s018_to_s032.zip` (4,780,938,300 bytes). They hold the NTU
Kinect 25-joint 3D skeleton modality; this protocol requires the OpenMMLab
HRNet-W32 17-joint COCO 2D coordinates and confidence scores.

## Inputs still required

| Input | Intended source | Intended local path | Known remote bytes | SHA-256 | Blocker |
|---|---|---|---:|---|---|
| NTU RGB+D 120 HRNet poses | [MotionBERT action-data instructions](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/docs/action.md#data); [pinned OpenMMLab path](https://download.openmmlab.com/mmaction/pyskl/data/nturgbd/ntu120_hrnet.pkl); [current OpenMMLab mirror](https://download.openmmlab.com/mmaction/v1.0/skeleton/data/ntu120_2d.pkl) | `ntu120_hrnet.pkl` | 1,238,461,428 | Pending local download | The researcher's NTU access request is pending. Download and use must wait until NTU grants access under its release agreement. |

## Checks required before completion

1. Confirm that the current NTU RGB+D release agreement has been accepted by
   the researcher and that use of the HRNet-derived release is authorized.
2. Download the full HRNet aggregate from either byte-matched OpenMMLab
   endpoint into the ignored data root, name it `ntu120_hrnet.pkl`, compute its
   SHA-256 before loading it, and record its byte size and UTC verification
   time.
3. Parse the container and verify the expected top-level `split` and
   `annotations` structures, all 114,480 canonical `frame_dir` identifiers,
   zero-based action labels, field ranges, duplicate absence, and presence of
   the exact 20 official anchors. Derive the locked one-shot memberships in
   memory and verify that each novel class has exactly one anchor. A truncated
   or merely syntactically valid pickle is not sufficient.
4. Re-run `git status`, `git check-ignore`, and
   `python scripts/verify_workspace.py`; only then update the task and gate.
