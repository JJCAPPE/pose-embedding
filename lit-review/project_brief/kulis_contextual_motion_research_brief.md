# Robust Contextual Metric Learning for Pose-Based Human Motion Retrieval

**Purpose:** meeting + research-prep notes for a proposed undergraduate research project with Prof. Brian Kulis.

**Working project title:** **Robust Contextual Metric Learning for Pose-Based Human Motion Retrieval under Pose-Estimation Noise**

**One-sentence pitch:**

> I want to extend contextual metric learning from image retrieval to human-motion retrieval by learning embeddings for pose sequences and testing whether neighborhood-based contextual similarity makes those embeddings more robust to noisy, incomplete, or camera-biased pose estimates.

---

## 0. Executive summary

The project idea evolved from a vague question — “can we compare two movements?” — into a stronger research problem:

> **Can we learn a motion embedding space where nearest-neighbor retrieval remains useful even when pose data is noisy?**

The application is not simply measuring similarity. The real application is **retrieval-augmented movement analysis**:

```text
new motion / pose sequence
→ embed into vector space
→ retrieve similar labeled/reference motions
→ infer action class, technique pattern, movement fault, rehab status, or performance cluster
```

This connects three areas:

1. **Brian Kulis’s metric-learning / retrieval work**
2. **Human pose estimation and temporal motion representation**
3. **Robustness to noise, camera angle, parallax, occlusion, and imperfect pose extraction**

The most compelling motivation is that pose estimation is an imperfect intermediate representation. If we train a motion retrieval model on clean skeletons, it may fail on real video-derived poses. Brian’s contextual metric-learning idea is interesting because it uses **neighborhood structure**, not only direct pairwise similarity. That may make it naturally suited to resisting pose noise and corrupted labels.

---

## 1. What we discussed so far

### Initial idea

The first idea was:

> Learn embeddings for human motion sequences so that similar movements are close together in vector space.

This felt interesting because it resembles a **RAG-style retrieval system**, but for motion instead of text.

Text RAG:

```text
query text → text embedding → retrieve similar documents → answer with retrieved context
```

Motion retrieval:

```text
query movement → motion embedding → retrieve similar movements → classify/explain/compare using retrieved examples
```

### Main concern

The concern was valid:

> Why do we care whether two movements are similar?

The stronger answer is:

> We care if similarity supports a downstream task: technique diagnosis, rehab tracking, fault retrieval, few-shot action classification, motion search, or comparison to reference examples.

So the project should not be framed as **movement similarity for its own sake**. It should be framed as **task-relevant retrieval of movement examples**.

### Stronger framing

The stronger framing became:

> Learn robust pose-sequence embeddings for movement retrieval, and test whether contextual metric learning improves robustness when pose data is noisy.

### Key insight

The issue with pose data is not just that it is temporal. It is that the pose sequence is usually an **estimated representation**, not ground truth. Real video-derived poses can contain:

- parallax error
- camera-angle distortion
- occlusion
- bad lighting
- body-part misdetections
- 2D-to-3D lifting error
- temporal jitter
- dropped joints
- inconsistent skeleton formats
- domain shift between datasets and real videos

That issue can become the research contribution.

---

## 2. Brian Kulis alignment

Brian Kulis’s research profile is strongly aligned with this project. His page describes his interests as large-scale optimization for machine-learning problems including **metric learning, content-based search, clustering, and online learning**, with applications in **audio and visual data**.

The proposed project fits because it is about:

- metric learning
- retrieval
- embeddings
- nearest-neighbor search
- robustness
- visual / motion data
- possible large-scale indexing of learned representations

The project should be presented as a **metric learning / retrieval project first**, and a sports/rowing/biomechanics project second.

Bad framing:

> I want to compare rowing strokes.

Better framing:

> I want to study whether contextual metric learning can improve robust retrieval of temporal human-motion embeddings under noisy pose estimates.

Rowing can be the motivating application, but not the dependency.

---

## 3. Simple explanation of Brian’s contextual metric-learning paper

### Paper

**Title:** *Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization*  
**Authors:** Christopher Liao, Theodoros Tsiligkaridis, Brian Kulis  
**Venue/version:** arXiv version; associated code repo states ICML 2023  
**Core topic:** supervised metric learning for image retrieval

### Problem the paper addresses

In standard supervised metric learning, the model learns an embedding space where:

```text
similar examples → close together
dissimilar examples → far apart
```

For image retrieval, this means:

```text
image → neural network → embedding vector → nearest-neighbor retrieval
```

The usual training logic is pairwise or triplet-based:

```text
Anchor A and positive P have same label → pull A and P closer
Anchor A and negative N have different labels → push A and N farther apart
```

The issue is that this can be brittle when labels are noisy or semantically inconsistent.

Example:

```text
Image A = red sports car
Image B = red sports car
Image C = blue truck, incorrectly labeled as sports car
```

A simple pairwise/triplet loss may force A and C closer just because the label says they match.

### Main idea

Brian’s paper adds **contextual similarity**.

Instead of asking only:

```text
Are A and B close?
```

it also asks:

```text
Do A and B have similar neighborhoods?
```

That means two samples are similar not only when their embeddings are directly close, but also when their **nearest-neighbor sets overlap**.

### Intuition

If two examples are truly semantically similar, they should be surrounded by similar examples.

```text
A's nearest neighbors: sports car, sports car, racing car, coupe
B's nearest neighbors: sports car, racing car, coupe, sports car
→ A and B are probably contextually similar
```

If labels are noisy:

```text
C is mislabeled as sports car,
but C's neighbors are trucks, vans, pickups.
→ C should not be pulled too aggressively into the sports-car cluster.
```

### Why this helps

Contextual similarity can be more robust because it considers **local structure** rather than only a single pairwise relationship.

A noisy pair can mislead a pairwise loss. But it is harder for one noisy label to completely corrupt the full neighborhood structure.

### What the paper contributed technically

The paper proposes a **contextual loss** that explicitly optimizes neighborhood similarity. Their final framework combines:

1. **Contextual loss** — makes neighborhood structure match label structure.
2. **Contrastive loss** — keeps ordinary pairwise distances meaningful.
3. **Similarity regularizer** — encourages better use of the embedding space.

The paper’s central technical challenge is that nearest-neighbor operations are discrete and non-differentiable:

- top-k selection
- greater-than comparisons
- set intersections
- reciprocal-neighbor logic

Neural networks need differentiable objectives for gradient descent. So the paper develops a way to optimize contextual similarity by using exact threshold-like behavior in the forward pass and a custom gradient-style approximation in the backward pass.

### Very simplified mathematical idea

For each sample `i`, compute its embedding:

```text
f_i ∈ R^d
```

Compute cosine similarity:

```text
s_ij = cosine(f_i, f_j)
```

Find the top-k neighbors of `i`:

```text
N_k(i)
```

Then define contextual similarity between `i` and `j` by neighborhood overlap:

```text
contextual_similarity(i, j) ≈ overlap(N_k(i), N_k(j))
```

If `i` and `j` have the same label, the model should increase contextual similarity.  
If they have different labels, the model should decrease contextual similarity.

### Why this matters for your project

Their method was designed for image retrieval. Your project would ask:

> Does contextual similarity also help in temporal pose-sequence retrieval, where inputs are naturally noisy?

That is a clean extension:

```text
original paper:
image → image embedding → contextual retrieval

proposed extension:
pose sequence → motion embedding → contextual retrieval under pose noise
```

---

## 4. Key ML concepts you need to understand

### 4.1 Embedding

An embedding is a learned vector representation of an object.

For text:

```text
sentence → [0.12, -0.44, 0.03, ...]
```

For an image:

```text
image → CNN/ViT → vector
```

For motion:

```text
pose sequence → temporal encoder → vector
```

The embedding vector should preserve the aspects of the input that matter for the task.

For this project, one motion clip becomes one vector:

```text
motion clip x_i → embedding f_i ∈ R^d
```

Possible dimensions:

- 128
- 256
- 512
- 768

The exact dimension is a design choice.

### 4.2 Metric learning

Metric learning trains a model so that distances in embedding space become meaningful.

The objective is not just classification. The objective is to make nearest-neighbor relationships useful.

```text
same class / similar behavior → small distance
different class / different behavior → large distance
```

Common distance/similarity functions:

- cosine similarity
- Euclidean distance
- squared Euclidean distance
- learned Mahalanobis-style distance

### 4.3 Contrastive loss

Contrastive loss works on pairs.

```text
positive pair: pull together
negative pair: push apart
```

Limitation:

- can be sensitive to bad labels
- pair construction matters
- does not directly optimize full ranking quality

### 4.4 Triplet loss

Triplet loss uses:

```text
anchor A
positive P: same class
negative N: different class
```

Goal:

```text
distance(A, P) + margin < distance(A, N)
```

Limitation:

- triplet mining matters a lot
- hard negatives can destabilize training
- can be computationally expensive

### 4.5 Supervised contrastive loss

Supervised contrastive learning generalizes contrastive learning to batches. For each anchor, all same-label examples in the batch are positives, and different-label examples are negatives.

This is a strong baseline for the proposed project.

### 4.6 Contextual similarity

Contextual similarity compares **neighborhood structure**.

Two samples are contextually similar if:

```text
they are close
and/or
they share similar nearest neighbors
and/or
they appear in reciprocal-neighbor relationships
```

This is the key idea from Brian’s paper.

### 4.7 Retrieval metrics

Since the task is retrieval, evaluation should use retrieval metrics, not only classification accuracy.

Important metrics:

- **Recall@1**: is the nearest retrieved item relevant?
- **Recall@5**: is any of the top 5 retrieved items relevant?
- **Recall@K**: generalized retrieval success.
- **mAP**: mean average precision, accounts for ranking quality across relevant items.
- **NDCG**: useful if relevance is graded rather than binary.

For a first version, use:

```text
Recall@1, Recall@5, Recall@10, mAP
```

### 4.8 Noisy labels vs noisy inputs

Important distinction:

**Noisy label:** the target annotation is wrong.

```text
video shows walking, label says running
```

**Noisy input:** the input representation is corrupted.

```text
pose sequence has jitter, missing wrists, wrong knees, bad 3D lifting
```

Brian’s paper focuses heavily on robustness to label noise and overfitting in image retrieval. Your extension could focus on **input noise in pose sequences**, while also optionally testing label noise.

That is one of the cleanest research differences.

---

## 5. The proposed research project

### Project title

**Robust Contextual Metric Learning for Pose-Based Human Motion Retrieval**

Longer version:

**Robust Contextual Metric Learning for Pose-Based Human Motion Retrieval under Pose-Estimation Noise**

### Core research question

> Can contextual metric learning improve the robustness of human-motion embeddings when pose sequences contain noise, missing joints, temporal jitter, or camera-induced distortion?

### Hypothesis

Contextual metric learning will be more robust than standard pairwise/triplet/supervised contrastive losses because it uses neighborhood structure rather than relying only on direct pairwise similarity.

### Basic pipeline

```text
pose sequence
    ↓
normalization / preprocessing
    ↓
temporal encoder
    ↓
fixed-length motion embedding
    ↓
nearest-neighbor retrieval
    ↓
retrieval evaluation under clean and noisy conditions
```

### What changes from Brian’s paper?

| Original contextual paper | Proposed extension |
|---|---|
| Static images | Temporal pose sequences |
| CNN image embeddings | Temporal motion embeddings |
| Image retrieval | Human-motion retrieval |
| Label noise and limited data | Pose-estimation noise, temporal distortion, missing joints, domain shift |
| Image datasets such as CUB, Cars, SOP, iNaturalist, In-Shop | Skeleton/motion datasets such as NTU RGB+D 120, AMASS, SportsPose, Human3.6M/H3WB |

### Main experimental comparison

Compare these training objectives:

1. Cross-entropy classification baseline, using penultimate layer as embedding
2. Contrastive loss
3. Triplet loss
4. Supervised contrastive loss
5. Contextual loss adapted from Brian’s paper
6. Hybrid contextual + contrastive loss

Then evaluate retrieval under increasing pose corruption.

---

## 6. Why this project is compelling

The key motivation is **noise in pose estimation**.

Real-world pose estimation is not perfectly reliable. If the model sees a video and extracts a skeleton, the skeleton may already contain structural error. That matters because the embedding model only sees the pose sequence.

### Sources of pose noise

| Noise source | Example |
|---|---|
| Parallax | Side-view vs angled-view movement changes apparent joint positions |
| Camera angle | Same motion appears different from front, side, diagonal |
| Camera distance | Small joint errors become magnified after scaling |
| Occlusion | Arms, hands, legs disappear behind body or objects |
| Lighting/background | Pose estimator loses confidence or swaps joints |
| Temporal jitter | Joints flicker frame to frame |
| Missing joints | Wrist, ankle, shoulder not detected in some frames |
| 2D-to-3D lifting error | Incorrect depth inferred from monocular video |
| Body morphology | Same action performed by different athletes appears geometrically different |
| Speed variation | Same action performed faster/slower changes temporal structure |

### Why contextual metric learning may help

A noisy pose sequence may be slightly wrong. Pairwise training may overreact to that single corrupted example.

Contextual training asks:

```text
Does this sequence live in a neighborhood of similar motions?
```

If one joint is noisy but the sequence still has similar neighbors, contextual similarity may preserve the correct structure.

This is the core intellectual reason to do the project.

---

## 7. Data strategy

The project should avoid relying on your own data collection at first.

Do **not** start with raw videos if avoidable. Start with datasets that already provide skeletons, 3D poses, motion capture, or structured pose representations.

### Candidate datasets

| Dataset | Modality | Scale / useful fact | Why useful | Caveat |
|---|---:|---:|---|---|
| **NTU RGB+D 120** | RGB, depth, IR, 3D skeletons | >114k video samples, 8M frames, 120 actions | Large skeleton-action dataset; good for retrieval by action class | Motions are broad daily actions, not sports-specific |
| **AMASS** | Unified mocap / SMPL motion | >40 hours, >300 subjects, >11k motions | Clean motion capture; excellent for pure motion representation | Less direct action-class retrieval; may require label handling |
| **SportsPose** | 3D sports pose | >176k 3D poses, 24 subjects, 5 sports activities | Direct sports/movement-analysis relevance | Smaller number of activities; check access format |
| **Human3.6M / H3WB** | 3D pose / whole-body keypoints | H3WB gives 133 whole-body keypoints on 100k images | Standard pose benchmark; useful for controlled experiments | More pose-estimation-focused than retrieval-focused |
| **FineGym** | Gymnastics videos with temporal action/subaction annotations | Fine-grained sport action hierarchy | Good for fine-grained action/motion reasoning | May require pose extraction unless using preprocessed features |
| **UCF101** | Raw videos | 101 action classes, >13k clips | Useful if later testing raw-video-to-pose pipeline | Not ideal for first phase because poses are not the native modality |

### Recommended first dataset path

Best first path:

1. **NTU RGB+D 120** for large-scale skeleton action retrieval.
2. Add controlled pose noise.
3. Evaluate retrieval robustness.
4. Optionally add SportsPose if the project needs stronger sports relevance.
5. Use AMASS if the project becomes more about motion representation than action-class retrieval.

### Should the project focus on one motion or many motions?

For the first research version, do **not** focus only on one motion like a baseball swing or rowing stroke.

Better first version:

> Train and evaluate on many labeled motion classes so retrieval metrics are well-defined.

Then, for a more specialized extension:

> Test whether the learned embedding space can distinguish subtle variations within one class, such as different types of sports movements or technique faults.

Why broad first?

- Easier evaluation
- More public data
- Less risk
- Better baseline comparison
- Less dependency on manual labels

Why narrow later?

- More biomechanical relevance
- More interesting real-world application
- Better connection to rowing/sports analytics

---

## 8. Temporal motion representation problem

A motion sequence is not a single image. It is a sequence:

```text
x ∈ R^(T × J × C)
```

Where:

- `T` = number of frames
- `J` = number of joints
- `C` = coordinates per joint, usually 2D or 3D

Example:

```text
T = 60 frames
J = 17 joints
C = 3 coordinates
x shape = 60 × 17 × 3
```

The model must convert this variable-length sequence into a fixed-length embedding vector:

```text
R^(T × J × C) → R^d
```

### The variable-length issue

Different motions may have different durations.

If you simply resample everything to the same length, you may distort speed.

Example:

```text
fast punch: 20 frames
slow punch: 80 frames
```

If both are normalized to 60 frames:

- the fast motion is stretched
- the slow motion is compressed
- speed information may be distorted

### Ways to handle different lengths

| Method | Description | Pros | Cons |
|---|---|---|---|
| Fixed-length resampling | Interpolate all clips to same T | Simple | Can distort speed/duration |
| Random temporal crops | Train on windows of same length | Good for batches | May lose global phase |
| Padding + mask | Keep variable length, mask padded frames | Preserves time | Requires model support |
| Temporal attention pooling | Model learns which frames matter | Flexible | More complex |
| Multi-scale pooling | Pool short/medium/long temporal features | Captures speed/structure | More engineering |
| Dynamic time warping baseline | Align sequences by phase | Good baseline | Not deep-learning-native |
| Include duration/speed features | Add explicit temporal metadata | Preserves speed info | Needs careful normalization |

### Recommended approach

For first version:

```text
normalize clips to fixed T
+ include temporal-speed augmentation
+ report this as a known limitation
```

For stronger version:

```text
use padding + attention pooling
and include original duration / speed statistics as features
```

### Important point for the meeting

You can say:

> One technical question I want to handle carefully is temporal normalization. If we force every movement to the same length, we may remove meaningful speed information. I would like to compare simple fixed-length resampling against masked variable-length temporal encoders or attention pooling.

---

## 9. Possible model architectures

### Input representation

Possible pose input formats:

1. Joint coordinates only:

```text
[x, y] or [x, y, z]
```

2. Joint coordinates + confidence scores:

```text
[x, y, confidence]
```

3. Joint coordinates + velocities:

```text
position, velocity, acceleration
```

4. Joint coordinates + bone vectors:

```text
joint position + relative limb vectors
```

5. Heatmap-based representation:

```text
pose heatmaps over time
```

### Architecture options

| Architecture | Description | Fit for project |
|---|---|---|
| Temporal CNN / TCN | 1D convolutions over time | Simple, efficient baseline |
| LSTM / GRU | Recurrent sequence model | Easy baseline, older but understandable |
| Transformer encoder | Self-attention over temporal tokens | Strong for long-range temporal dependencies |
| ST-GCN | Graph convolution over skeleton joints and time | Very natural for skeleton data |
| MST-GCN | Multi-scale graph-temporal model | Stronger skeleton baseline |
| MotionBERT / DSTformer-style encoder | Transformer for human motion representations | Strong modern direction |
| PoseC3D-style approach | 3D spatiotemporal heatmap representation | Interesting because it explicitly claims robustness to pose noise |

### Recommended architecture progression

Do not start with the most complex model.

Suggested progression:

1. **Simple temporal encoder baseline**
   - MLP over flattened normalized poses or TCN
   - proves the pipeline works

2. **ST-GCN or Transformer encoder**
   - better temporal/spatial modeling

3. **Contextual metric-learning loss**
   - plug into the embedding output

4. **Noise robustness experiments**
   - the actual research contribution

### Embedding output

The model should output one vector per sequence:

```text
pose_sequence → encoder → pooled_hidden_state → projection_head → L2-normalized embedding
```

Example:

```python
embedding = model(sequence)          # shape: [batch_size, d]
embedding = normalize(embedding)     # for cosine similarity
```

---

## 10. Adapting Brian’s contextual loss to motion

### Original setting

```text
image batch → CNN → image embeddings → contextual loss
```

### New setting

```text
pose-sequence batch → temporal encoder → motion embeddings → contextual loss
```

The loss itself may not need to know whether the embedding came from an image or a pose sequence. It only sees embeddings and labels.

So the model-specific part changes:

```text
CNN image encoder → temporal pose encoder
```

The metric-learning objective can remain conceptually similar:

```text
compute embedding similarities
compute neighbor sets
compute contextual similarity matrix
match contextual similarity to label similarity
```

### Pseudocode

```python
# x: [batch, time, joints, coords]
# y: [batch]

z = motion_encoder(x)          # [batch, d]
z = l2_normalize(z)            # cosine-ready embeddings

S = z @ z.T                    # pairwise cosine similarities
Y = same_label_matrix(y)       # Y[i,j] = 1 if same label else 0

W_context = contextual_similarity(S, k=samples_per_class)

loss_context = mse(W_context, Y)
loss_contrast = contrastive_loss(z, y)
loss = loss_context + lambda_c * loss_contrast + lambda_r * regularizer
```

### Important implementation detail

Brian’s contextual loss depends on batch structure. In the paper’s setup, k is tied to the number of samples per class in a mini-batch. That means batch sampling matters.

You may need batches like:

```text
N classes per batch
M samples per class
```

Example:

```text
32 action classes × 4 sequences per class = batch size 128
```

For motion datasets, this may be feasible depending on memory and sequence length.

---

## 11. Noise experiments: the core contribution

This should be the centerpiece.

### Clean training / noisy testing

Train on clean or lightly augmented skeleton sequences. Test on corrupted skeleton sequences.

Question:

> Which loss produces embeddings whose retrieval quality degrades the least as pose noise increases?

### Noise types to simulate

| Noise type | Implementation | Real-world analog |
|---|---|---|
| Gaussian joint jitter | Add noise to joint coordinates | Pose estimator uncertainty |
| Joint dropout | Mask random joints | Occlusion / missed detection |
| Limb dropout | Mask connected joints | Arm/leg hidden from camera |
| Temporal jitter | Randomly perturb frame order or positions | Frame-level pose instability |
| Frame dropout | Remove frames | Tracking failure / low FPS |
| Camera rotation | Rotate 3D skeleton | Viewpoint shift |
| Scaling error | Random body-scale changes | Distance/camera calibration error |
| Left-right swap | Swap symmetric joints occasionally | Pose-estimator error |
| 2D projection distortion | Project 3D to 2D under different camera assumptions | Parallax / monocular ambiguity |
| Speed perturbation | Time stretch/compress | Different execution speeds |

### Robustness curve

For each method, plot:

```text
noise level → Recall@1 / Recall@5 / mAP
```

The best result is not necessarily highest clean performance. The strongest result is:

> Contextual metric learning degrades more gracefully under pose corruption.

### Example experimental table

| Method | Clean R@1 | Mild noise R@1 | Medium noise R@1 | Heavy noise R@1 | Robustness drop |
|---|---:|---:|---:|---:|---:|
| Cross-entropy embedding | TBD | TBD | TBD | TBD | TBD |
| Triplet loss | TBD | TBD | TBD | TBD | TBD |
| SupCon | TBD | TBD | TBD | TBD | TBD |
| Contextual loss | TBD | TBD | TBD | TBD | TBD |
| Hybrid contextual + contrastive | TBD | TBD | TBD | TBD | TBD |

---

## 12. Evaluation design

### Retrieval task

For each query motion, retrieve top-k nearest motions from a gallery.

A retrieval is correct if the retrieved sequence shares the same label, action, sub-action, or metadata class.

```text
query: "throw"
retrieved top-5: throw, throw, punch, throw, kick
Recall@1 = correct
Recall@5 = correct
```

### Metrics

Use:

- Recall@1
- Recall@5
- Recall@10
- mAP
- robustness drop under noise
- cross-view retrieval performance
- cross-subject retrieval performance

### Dataset splits

Possible splits:

1. **Cross-subject**
   - train on some people
   - test on unseen people

2. **Cross-view**
   - train on some camera views
   - test on unseen views

3. **Cross-noise**
   - train clean
   - test noisy

4. **Cross-dataset**
   - train on one dataset
   - test/fine-tune on another

### Strongest evaluation framing

The strongest version is:

> We evaluate not just whether the embedding works on clean data, but whether its neighborhood structure remains semantically meaningful under controlled pose corruption and domain shift.

---

## 13. Implementation paths

### Path A — low-risk version

**Goal:** build a complete project with minimal dependency risk.

Use:

- NTU RGB+D 120 skeletons
- PyTorch temporal encoder
- simple baselines
- contextual loss adaptation
- synthetic noise experiments

Deliverable:

- reproducible repo
- retrieval metrics
- robustness plots
- short paper-style report

This is probably the best first version.

### Path B — sports-focused version

**Goal:** make the project more obviously connected to athletics.

Use:

- SportsPose
- possibly FineGym if willing to process video
- maybe add a small rowing dataset later

Deliverable:

- sports movement retrieval
- noise robustness on dynamic sports poses

Risk:

- smaller dataset
- more dataset-specific preprocessing

### Path C — representation-learning version

**Goal:** make it more ML-research-heavy.

Use:

- AMASS
- self-supervised or supervised contrastive objectives
- possibly action labels from AMASS subsets if available

Deliverable:

- motion representation benchmark
- embeddings evaluated on retrieval and clustering

Risk:

- label structure may be messier

### Path D — real-video robustness version

**Goal:** directly address real pose-estimation pipelines.

Use:

```text
raw video → MMPose / ViTPose / MediaPipe / MotionBERT → pose sequence → embedding
```

Deliverable:

- compare clean mocap/skeleton data vs video-extracted pose data

Risk:

- pose extraction becomes a large project by itself
- may distract from metric learning

### Recommended path

Start with **Path A**.

Then pitch optional extensions:

1. Add SportsPose for sports-specific relevance.
2. Add real video-derived poses only after the retrieval pipeline works.
3. Add rowing data only as a later demo, not as the research foundation.

---

## 14. Technology stack

### Core ML stack

- Python
- PyTorch
- NumPy
- scikit-learn
- pandas
- matplotlib
- tqdm

### Metric learning

- PyTorch Metric Learning
- custom implementation of contextual loss
- Brian’s GitHub repo as reference implementation

### Vector retrieval

- FAISS for fast nearest-neighbor retrieval
- brute-force cosine similarity for small experiments
- optional later: HNSW / vector DB if making a retrieval demo

### Pose / motion tools

- PyTorch Geometric if using graph neural networks
- MMAction2 if using skeleton-action-recognition baselines
- MMPose or ViTPose only for optional raw-video extension
- MotionBERT as a possible reference architecture / pretrained representation direction

### Experiment tracking

- Weights & Biases or MLflow
- YAML/Hydra configs
- fixed random seeds
- saved checkpoints

### Repo structure

```text
motion-contextual-metric-learning/
  README.md
  configs/
    ntu_tcn_contextual.yaml
    ntu_stgcn_supcon.yaml
  data/
    README.md
    preprocessing/
  src/
    datasets/
      ntu.py
      sports_pose.py
    models/
      tcn.py
      stgcn.py
      transformer.py
    losses/
      contrastive.py
      supervised_contrastive.py
      contextual.py
    eval/
      retrieval.py
      robustness.py
    noise/
      corruptions.py
    train.py
    evaluate.py
  notebooks/
    embedding_visualization.ipynb
    retrieval_examples.ipynb
  outputs/
    figures/
    tables/
  paper_notes/
    literature_review.md
```

---

## 15. Computational difficulty

Training an embedding model is feasible, but the compute depends heavily on:

- dataset size
- sequence length
- model architecture
- batch size
- whether using raw video or skeletons

### Why skeletons are manageable

Skeleton sequences are much lighter than raw video.

Raw video:

```text
T × H × W × 3
```

Skeleton sequence:

```text
T × J × C
```

Example:

```text
60 frames × 25 joints × 3 coords = 4,500 numbers
```

That is much smaller than 60 RGB frames.

### Expected compute

For a first version:

- small TCN/LSTM: laptop/GPU feasible for prototyping
- ST-GCN/Transformer: GPU recommended
- large NTU training: use BU GPU, Colab Pro, Kaggle GPU, or cloud GPU if available

### Practical target

Aim for:

- first baseline running on a subset within a day
- full training on one GPU
- no dependency on multi-GPU training

### Batch-size issue

Contextual loss benefits from structured batches with multiple samples per class. Larger batches help because the method computes neighborhood structure inside the batch.

Possible compromise:

```text
16 classes × 4 samples = batch 64
or
32 classes × 4 samples = batch 128
```

If memory is tight:

- shorten sequence length
- use smaller model
- use mixed precision
- use gradient accumulation

---

## 16. Literature review roadmap

### Literature-review buckets

You should review papers in five groups.

#### A. Brian / metric learning / contextual similarity

Core questions:

- What is metric learning?
- What are contrastive/triplet/proxy/AP losses?
- What problem does contextual similarity solve?
- Why is neighborhood structure useful?

Start with:

- Kulis paper: *Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization*
- Kulis survey: *Metric Learning: A Survey*
- *A Metric Learning Reality Check*
- Supervised Contrastive Learning
- ProxyNCA / ProxyAnchor / Multi-Similarity Loss / Smooth-AP / Fast-AP if needed

#### B. Skeleton-based action recognition

Core questions:

- How are skeleton sequences represented?
- What architectures are standard?
- How do models capture spatial and temporal structure?

Start with:

- ST-GCN
- MST-GCN
- ST-TR / skeleton transformers
- PoseC3D
- surveys on 3D skeleton-based action recognition

#### C. Human motion representation learning

Core questions:

- How do models learn general-purpose motion embeddings?
- What is the role of pretraining?
- Can motion representations transfer across tasks?

Start with:

- MotionBERT
- AMASS-related motion representation papers
- contrastive/self-supervised human motion representation papers

#### D. Pose-estimation noise and robustness

Core questions:

- What are common pose-estimation failure modes?
- How do pose-based recognition systems degrade under noise?
- Which representations are robust to noisy skeletons?

Start with:

- PoseC3D, because it explicitly discusses robustness to pose-estimation noise
- papers on cross-view/cross-subject skeleton action recognition
- papers on noisy keypoints / missing joints

#### E. Retrieval systems / vector search

Core questions:

- How are embeddings indexed and searched?
- What metrics are used for retrieval quality?
- How do brute-force and approximate nearest-neighbor retrieval differ?

Start with:

- FAISS
- nearest-neighbor search
- vector databases
- retrieval metrics: Recall@K, mAP, NDCG

---

## 17. Specific search queries for literature review

Use these exact search queries:

```text
contextual metric learning retrieval supervised metric learning Kulis
contextual similarity optimization metric learning image retrieval
metric learning reality check deep metric learning
supervised contrastive learning embeddings retrieval
skeleton based action recognition ST-GCN NTU RGB+D
spatial temporal graph convolutional networks skeleton action recognition
PoseC3D skeleton action recognition pose estimation noise robustness
MotionBERT human motion representations pose sequence embeddings
human motion retrieval pose sequence embedding metric learning
contrastive learning human motion representation skeleton sequences
robust skeleton action recognition noisy joints missing joints
cross-view skeleton action recognition robustness
AMASS motion representation learning contrastive
NTU RGB+D 120 skeleton action recognition retrieval
SportsPose 3D sports pose dataset
FAISS vector similarity search embeddings retrieval
```

---

## 18. Possible research questions

### Main question

> Does contextual metric learning improve pose-based human-motion retrieval robustness under pose-estimation noise?

### Subquestions

1. Does contextual loss improve clean retrieval performance over contrastive/triplet/SupCon baselines?
2. Does contextual loss reduce performance degradation under synthetic joint noise?
3. Which noise types are most damaging?
4. Does contextual similarity help more under label noise, input noise, or both?
5. Does the benefit depend on the temporal encoder architecture?
6. Does the method generalize across subjects or camera views?
7. Does temporal normalization distort speed-sensitive motions?
8. Are neighborhood-based embeddings more stable across pose-estimation models?
9. Does combining contextual loss with confidence-weighted joints improve robustness?
10. Can the embedding space support retrieval-augmented movement explanation?

---

## 19. Possible experimental hypotheses

### Hypothesis 1

Contextual metric learning improves Recall@K under noisy pose perturbations compared with standard contrastive or triplet losses.

### Hypothesis 2

The advantage of contextual loss is larger under medium noise than under clean data, because neighborhood information becomes more valuable when individual pairwise similarities are unreliable.

### Hypothesis 3

Pose noise affecting distal joints — wrists, ankles — hurts fine-grained actions more than torso noise.

### Hypothesis 4

Models trained with joint dropout and temporal jitter augmentations learn more stable embeddings under real pose-estimation noise.

### Hypothesis 5

Cross-view retrieval benefits from contextual similarity because true semantic neighborhoods are partially preserved even when direct geometric similarity changes.

---

## 20. Possible implementation plan

### Phase 1 — Reproduce conceptual baseline

- Read Brian’s paper carefully.
- Inspect his GitHub repo.
- Understand the loss implementation.
- Run or inspect a small image-retrieval baseline if feasible.

Deliverable:

- notes on contextual loss
- simplified PyTorch implementation

### Phase 2 — Build motion retrieval pipeline

- Load skeleton dataset.
- Normalize skeletons.
- Create train/test splits.
- Implement temporal encoder.
- Train baseline embedding model.
- Evaluate Recall@K and mAP.

Deliverable:

- clean-data motion retrieval baseline

### Phase 3 — Add contextual loss

- Adapt contextual loss to motion embeddings.
- Ensure batch sampler has `N classes × M samples`.
- Compare against triplet/SupCon/contrastive.

Deliverable:

- first contextual-vs-baseline comparison

### Phase 4 — Add pose noise benchmark

- Implement synthetic corruptions.
- Evaluate all methods under increasing noise.
- Plot robustness curves.

Deliverable:

- central experimental result

### Phase 5 — Optional extensions

- SportsPose experiments.
- Real video-to-pose pipeline.
- Cross-dataset generalization.
- Retrieval demo with FAISS.
- Rowing-specific proof of concept.

---

## 21. Questions to ask Brian

### Project framing questions

1. Does this extension from image retrieval to temporal pose retrieval seem aligned with your current research interests?
2. Would you frame the novelty more as **contextual metric learning for temporal data** or as **robustness to pose-estimation noise**?
3. Should the first version focus on clean skeleton benchmarks, synthetic noise, or real video-derived poses?

### Technical questions

4. In your contextual-loss paper, what part of the method do you think is most transferable outside images?
5. Does the batch-wise definition of contextual similarity create problems for motion datasets with fewer examples per class?
6. Would you recommend keeping the original contextual loss mostly unchanged and swapping the encoder, or modifying the contextual definition for temporal sequences?
7. Should k be tied to samples per class in the batch, or should it be tuned differently for motion?
8. Would cross-view retrieval be a better evaluation than synthetic noise?

### Scope questions

9. What would be a reasonable one-semester deliverable?
10. Would you prefer a reproduction/extension of the ICML paper first, or a new motion-specific implementation from the start?
11. Is this a good undergraduate research project if scoped around reproducible experiments rather than a new theory contribution?

### Dataset questions

12. Would NTU RGB+D 120 be a good first dataset?
13. Would SportsPose be too narrow or useful because of the sports connection?
14. Would AMASS be better for motion representation, even if labels are less straightforward?

---

## 22. Meeting pitch versions

### 15-second version

> I’m interested in extending contextual metric learning from image retrieval to pose-based motion retrieval. The core idea is to learn embeddings for pose sequences and test whether contextual neighborhood structure makes those embeddings more robust to noisy pose estimates.

### 30-second version

> Your contextual metric-learning paper uses neighborhood structure to make image retrieval more robust. I’d like to explore whether that idea transfers to human-motion retrieval, where each input is a temporal pose sequence rather than an image. The motivation is that pose estimation is naturally noisy because of camera angle, parallax, occlusion, missing joints, and temporal jitter. I want to test whether contextual similarity helps preserve useful retrieval neighborhoods under those corruptions.

### 60-second version

> I’d like to propose a project that extends contextual metric learning from image retrieval to pose-based human-motion retrieval. The model would take a sequence of skeleton poses, use a temporal encoder to produce one fixed-length embedding vector, and then retrieve similar movements by nearest-neighbor search. The part I find most interesting is robustness: pose data extracted from video is noisy because of parallax, camera angle, occlusion, temporal jitter, and imperfect 2D-to-3D lifting. So the research question would be whether contextual similarity — using neighborhood structure rather than only pairwise distances — can make motion embeddings more stable under pose-estimation noise. I’d start with public skeleton datasets like NTU RGB+D 120 or SportsPose, compare against contrastive/triplet/supervised contrastive baselines, and evaluate retrieval under controlled pose corruptions.

---

## 23. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Dataset access is hard | Start with a well-used skeleton dataset and verify access immediately |
| Contextual loss implementation is complex | Start from Brian’s repo and reimplement minimal version |
| Training is expensive | Use skeletons, not raw video; start with small TCN baseline |
| Retrieval labels are too coarse | Begin with action-class retrieval; later add fine-grained/sports-specific data |
| Temporal normalization distorts motion | Compare fixed-length resampling with masked variable-length pooling |
| Noise experiments feel artificial | Use synthetic noise first, then validate with real pose-estimator outputs if possible |
| Project becomes too broad | Keep the first contribution narrow: contextual loss vs baselines under pose noise |

---

## 24. What would count as a strong final result?

A strong final result would be a paper-style claim such as:

> Contextual metric learning improves robustness of pose-based human-motion retrieval under joint jitter, missing joints, and cross-view perturbations compared with standard contrastive/triplet/supervised contrastive baselines.

Even stronger:

> The contextual model has similar clean-data performance but significantly smaller retrieval degradation as pose noise increases.

Best-case result:

> Neighborhood-based contextual similarity is especially useful when individual pairwise similarities are unreliable, suggesting that contextual metric learning is a good fit for noisy pose-estimation pipelines.

---

## 25. What to read first

### Must-read

1. Brian Kulis paper: *Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization*
2. GitHub repo for the paper
3. ST-GCN paper
4. PoseC3D paper
5. MotionBERT paper
6. NTU RGB+D 120 dataset paper
7. SportsPose dataset paper

### Useful next reads

8. Supervised Contrastive Learning
9. A Metric Learning Reality Check
10. PyTorch Metric Learning paper/docs
11. AMASS dataset paper
12. Skeleton-based action recognition survey
13. FAISS paper/docs

---

## 26. Source notes and references

These are the sources checked while preparing this brief.

### Brian Kulis / contextual metric learning

- Brian Kulis personal BU page: https://people.bu.edu/bkulis/
- BU CDS profile: https://www.bu.edu/cds-faculty/profile/brian-kulis/
- *Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization*: https://arxiv.org/abs/2210.01908
- GitHub repo: https://github.com/Chris210634/metric-learning-using-contextual-similarity

### Metric learning background

- *A Metric Learning Reality Check*: https://arxiv.org/abs/2003.08505
- *Supervised Contrastive Learning*: https://arxiv.org/abs/2004.11362
- *PyTorch Metric Learning*: https://arxiv.org/abs/2008.09164

### Pose / motion / skeleton datasets and models

- NTU RGB+D 120: https://arxiv.org/abs/1905.04757
- AMASS: https://arxiv.org/abs/1904.03278
- SportsPose: https://arxiv.org/abs/2304.01865
- H3WB / Human3.6M WholeBody: https://arxiv.org/abs/2211.15692
- FineGym: https://arxiv.org/abs/2004.06704
- UCF101: https://arxiv.org/abs/1212.0402
- ST-GCN: https://arxiv.org/abs/1801.07455
- MST-GCN: https://arxiv.org/abs/2206.13028
- Skeleton Spatial-Temporal Transformer: https://arxiv.org/abs/2008.07404
- MotionBERT: https://arxiv.org/abs/2210.06551
- PoseC3D / Revisiting Skeleton-based Action Recognition: https://arxiv.org/abs/2104.13586
- Survey on 3D skeleton-based action recognition: https://arxiv.org/abs/2002.05907

### Retrieval / vector search

- FAISS paper: https://arxiv.org/abs/2401.08281

---

## 27. Final thesis of the project

The project is not about saying two movements are “similar” in a vague way.

It is about learning whether **contextual neighborhood structure** can make motion embeddings robust enough for real retrieval tasks when pose inputs are imperfect.

The strongest statement is:

> Human-motion retrieval from pose sequences is vulnerable to pose-estimation noise. Contextual metric learning may help because it optimizes neighborhood structure, not just individual pairwise distances. Extending Brian Kulis’s contextual loss from image retrieval to temporal pose embeddings is therefore both technically natural and practically motivated.
