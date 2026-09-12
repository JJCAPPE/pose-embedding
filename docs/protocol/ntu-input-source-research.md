# NTU input source research

Observed 2026-09-11 (America/New_York). This note uses only dataset-owner,
MotionBERT-author, and OpenMMLab sources. No NTU archive or pose pickle was
downloaded during this audit.

## Decision

1. Neither required pickle is stored as a file in an official GitHub tree.
   GitHub hosts the code and documentation; the actual downloads are external.
2. The full HRNet-derived input is available from OpenMMLab. The current
   MMAction2 name, `ntu120_2d.pkl`, and MotionBERT's older PYSKL name,
   `ntu120_hrnet.pkl`, have the same byte count, ETag, and `Content-MD5` in
   OpenMMLab's HTTP metadata. After NTU access is approved, one download is
   sufficient; save it under the filename expected by this project and compute
   its SHA-256 locally.
3. The two Google Drive archives contain Kinect-derived 25-joint 3D `.skeleton`
   data. They are not the 17-joint, 2D HRNet detections MotionBERT's action
   loader consumes, so they do not substitute for the full HRNet pickle or its
   one-shot view.
4. The public one-shot definition is sufficient to construct the membership of
   the gallery and test sets deterministically at runtime from the full HRNet
   aggregate. A separate pickle is therefore not algorithmically necessary.
   It is still necessary to obtain the authors' pickle if byte-for-byte
   reproduction of their unpublished packaging is a requirement.
5. Do not fetch, generate, or redistribute an NTU-derived aggregate while the
   access request is pending. The NTU page requires registration, a request,
   and acceptance of its Release Agreement, and says dataset derivation or
   generation requires express ROSE Lab permission.

## Full HRNet-derived pose aggregate

MotionBERT's pinned [action-recognition instructions](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/docs/action.md#data)
do not embed `ntu120_hrnet.pkl` in GitHub; they link to the PYSKL/OpenMMLab CDN.
The pinned [PYSKL data documentation](https://github.com/kennymckormick/pyskl/blob/f2bf3a6b08e2e8dec744692d64efdb187fd6719a/tools/data/README.md#download-the-pre-processed-skeletons)
describes it as NTU RGB+D 120 2D skeleton data and specifies a COCO-style
17-joint `keypoint` array plus `keypoint_score`.

OpenMMLab currently documents the equivalent maintained download as
[`ntu120_2d.pkl`](https://download.openmmlab.com/mmaction/v1.0/skeleton/data/ntu120_2d.pkl)
in the [MMAction2 skeleton README](https://github.com/open-mmlab/mmaction2/blob/a5a167dff2399e2d182a60332325f9c0d4663517/tools/data/skeleton/README.md#prepare-annotations).
That README states that the 2D annotations use Faster R-CNN for person
detection and HRNet-w32 for pose estimation.

Unauthenticated `HEAD` responses from the two OpenMMLab URLs returned:

| URL name | Bytes | ETag | `Content-MD5` |
| --- | ---: | --- | --- |
| [`ntu120_hrnet.pkl`](https://download.openmmlab.com/mmaction/pyskl/data/nturgbd/ntu120_hrnet.pkl) | 1,238,461,428 | `31C0EFD891F18B942403DE3376CEE000` | `McDv2JHxi5QkA94zds7gAA==` |
| [`ntu120_2d.pkl`](https://download.openmmlab.com/mmaction/v1.0/skeleton/data/ntu120_2d.pkl) | 1,238,461,428 | `31C0EFD891F18B942403DE3376CEE000` | `McDv2JHxi5QkA94zds7gAA==` |

The base64 `Content-MD5` decodes to the ETag value in lowercase. This is strong
server-side evidence that the URLs alias the same payload, but it is not the
required SHA-256 verification. Compute SHA-256 after the authorized download;
there is no need to download both aliases.

The current MMAction2 README also documents a way to regenerate 2D poses from
the RGB videos, but warns that updated MMPose versions may produce slightly
different results. Regeneration is therefore a fallback for a new,
explicitly-versioned input, not an exact replacement for the locked upstream
aggregate.

## Supplied Google Drive archives

The dataset authors' [NTURGB-D repository](https://github.com/shahroudy/NTURGB-D/blob/ac2ebc87e6e9777ea6bac67e65e53b325b903f74/README.md#how-to-download-the-datasets)
links both supplied Drive IDs as the optional raw skeleton downloads. Public
Drive metadata, inspected without downloading the archive bodies, identifies
them as:

| Drive ID | Public metadata filename | Bytes |
| --- | --- | ---: |
| [`1CUZnBtYwifVXS21yVg62T-vrPVayso5H`](https://drive.google.com/file/d/1CUZnBtYwifVXS21yVg62T-vrPVayso5H/view) | `nturgbd_skeletons_s001_to_s017.zip` | 6,181,024,200 |
| [`1tEbuaEqMxAV7dNc4fqu1O4M7mC6CJ50w`](https://drive.google.com/file/d/1tEbuaEqMxAV7dNc4fqu1O4M7mC6CJ50w/view) | `nturgbd_skeletons_s018_to_s032.zip` | 4,780,938,300 |

The authors describe NTU's skeletal modality as Kinect V2 3D coordinates for
25 body joints. MMAction2 separately labels its raw-skeleton conversion path as
3D and "only applicable to GCN backbones"; that path produces the 3D annotation
aggregate rather than HRNet detections. In contrast, MotionBERT's pinned
[`coco2h36m` conversion and dataset loader](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/lib/data/dataset_action.py#L22-L151)
index a 17-joint COCO layout and concatenate a `keypoint_score` channel.

Using the Drive files would therefore require a different joint mapping,
confidence convention, and input provenance. That is a scientific protocol
change, not a recovery path for the missing MotionBERT inputs. Their SHA-256
values were not computed because the archive bodies were deliberately not
downloaded.

## One-shot split: what is and is not missing

MotionBERT's pinned documentation sends users to a
[`1drv.ms` folder](https://1drv.ms/f/s!AvAdh0LSjEOlfi-hqlHxdVMZxWM) for the
one-shot split. On 2026-09-11 the short URL redirected to OneDrive item
`A5438CD242871DF0!126`, after which an unauthenticated request returned HTTP
403. The official MotionBERT Git tree contains the loader reference but no
`ntu120_hrnet_oneshot.pkl`, and no checksum is published in the inspected
official documentation.

The separate pickle is only used as a container for annotations plus two lists.
The pinned [`train_action_1shot.py`](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/train_action_1shot.py#L135-L144)
loads `oneshot_train` and `oneshot_val`. The pinned
[`ActionDataset` implementation](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/lib/data/dataset_action.py#L132-L151)
uses the selected split only as a list of `frame_dir` identifiers with which to
filter the pickle's `annotations` list. The same training script reads the full
HRNet aggregate for the 100 auxiliary classes, and its
[`NTURGBD1Shot` class](https://github.com/Walter0807/MotionBERT/blob/705d3a95354db8bdb696b3492e47a3b5537174ff/lib/data/dataset_action.py#L181-L199)
hard-codes the 20 zero-based novel labels.

The dataset authors' locked [official one-shot protocol](https://github.com/shahroudy/NTURGB-D/blob/ac2ebc87e6e9777ea6bac67e65e53b325b903f74/README.md#evaluation-protocol-of-one-shot-action-recognition-on-ntu-rgbd-120)
defines all relevant membership:

- novel actions are A1, A7, A13, ..., A115 (every sixth action beginning at
  A1);
- it names exactly one exemplar `frame_dir` for each of those 20 actions;
- every remaining sample of those novel actions is evaluation data; and
- every sample of the other 100 actions is auxiliary data.

Consequently, after the full aggregate is authorized and validated, the
project can preserve its annotation order and deterministically compute:

```text
oneshot_train = the 20 official exemplar IDs, in published order
oneshot_val   = full annotations whose label is novel and whose frame_dir is
                not an exemplar, preserving full-aggregate order
auxiliary     = full annotations whose label is not novel, preserving
                full-aggregate order
```

This can be a runtime view over the authorized aggregate; writing another
pickle is technically unnecessary. Before relying on it, validate that all 20
exemplar identifiers occur exactly once, labels agree, the three sets are
disjoint, and every full annotation belongs to exactly one role. Because the
authors' OneDrive pickle is unreadable, exact byte identity, annotation order,
and any unpublished exclusions in that file remain unverified. If matching the
authors' packaging rather than the public protocol is required, ask the
MotionBERT maintainers to restore the share and publish a SHA-256.

## Access and licensing boundary

The current [NTU dataset page](https://rose1.ntu.edu.sg/dataset/actionRecognition/)
says researchers must register, submit a request, and accept the Release
Agreement before downloading. It limits the dataset to academic,
non-commercial research and says redistribution, derivation, or generation of
a new dataset requires express ROSE Lab permission.

The OpenMMLab URLs are technically reachable without authentication, and the
dataset authors publish the raw-skeleton Drive links, but reachability is not a
license grant. Until the pending NTU request is approved and its agreement is
accepted, this audit should stop at URL and HTTP-metadata checks. After approval,
keep downloaded pickles below `POSE_EMBED_DATA_ROOT`, never commit them, and
record the accepted terms and local SHA-256. If the agreement does not clearly
cover use of the OpenMMLab HRNet derivative or construction of a local split
view, obtain written clarification from ROSE Lab. This is a provenance and
compliance recommendation, not legal advice.

## Recommended acquisition sequence

1. Wait for NTU approval and retain evidence of the accepted Release Agreement
   outside Git.
2. Download one OpenMMLab 2D file, preferably the currently documented
   `ntu120_2d.pkl`, into the ignored data root under the project's expected
   `ntu120_hrnet.pkl` name.
3. Record its final byte count and `shasum -a 256`; then load it only as a
   trusted pickle and validate the documented `split`/`annotations` schema,
   COCO-17 coordinates, confidence scores, unique `frame_dir` values, and the
   20 official exemplars.
4. Prefer the locked, in-memory split construction above if protocol and
   licensing review approve it. Otherwise, ask the MotionBERT maintainers for
   restored authorized access to `ntu120_hrnet_oneshot.pkl` and its SHA-256.
5. Do not download the two 3D Drive archives for this experiment; they add about
   10.96 GB and do not satisfy the frozen HRNet-input requirement.

## Public-source checksums

These hashes cover only the small public source documents, not licensed data:

| Source | SHA-256 |
| --- | --- |
| [NTURGB-D README at `ac2ebc8`](https://raw.githubusercontent.com/shahroudy/NTURGB-D/ac2ebc87e6e9777ea6bac67e65e53b325b903f74/README.md) | `1968e07f83bd7e9ea2ac6f9797bbfe880e59828b7b0f1644b3e5736ea68acc33` |
| [MotionBERT action docs at `705d3a9`](https://raw.githubusercontent.com/Walter0807/MotionBERT/705d3a95354db8bdb696b3492e47a3b5537174ff/docs/action.md) | `b716e4bfde34cd73b1cddea621039be84c66697943064aafa7cc26762af0d244` |
| [MotionBERT dataset loader at `705d3a9`](https://raw.githubusercontent.com/Walter0807/MotionBERT/705d3a95354db8bdb696b3492e47a3b5537174ff/lib/data/dataset_action.py) | `963bf234ac0ec449e747bafdfd5f492c72d964e973761a11f817e94af32e8bde` |
| [MotionBERT one-shot trainer at `705d3a9`](https://raw.githubusercontent.com/Walter0807/MotionBERT/705d3a95354db8bdb696b3492e47a3b5537174ff/train_action_1shot.py) | `13610fa5e21ff012ddb8f2c51d312d2080b92c12bd59cf79a8726e655348fddb` |
| [PYSKL data README at `f2bf3a6`](https://raw.githubusercontent.com/kennymckormick/pyskl/f2bf3a6b08e2e8dec744692d64efdb187fd6719a/tools/data/README.md) | `c6daa97bc0fa8e8cdbb0a6b3e5b6ae43b2184902cb3af355fd94d9e35093f726` |
| [MMAction2 skeleton README at `a5a167d`](https://raw.githubusercontent.com/open-mmlab/mmaction2/a5a167dff2399e2d182a60332325f9c0d4663517/tools/data/skeleton/README.md) | `059afe3758a635be6345242298c4c94768f226ae3d95b53614ce64284acebb6e` |
