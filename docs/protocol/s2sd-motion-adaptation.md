# R-Margin + S2SD: declared motion adaptation

Recipe: `roth2021_rmargin_msdfa_cub_motion`. Source audit: 2026-09-26.
This is the CUB/Cars **MSDFA** architecture applied to motion with the CUB
R-Margin constants. It does not substitute Multi-Similarity for the R-Margin
row. Implementation and synthetic checks do not establish a dataset result.
Real GPU memory profiling and development selection remain required.

## Sources and reuse boundary

- [S2SD paper, Sections 3–5 and Table 2](https://proceedings.mlr.press/v139/roth21a/roth21a.pdf).
- [Supplement, Sections B and E](https://proceedings.mlr.press/v139/roth21a/roth21a-supp.pdf).
- [Official source at `1ef26e4e273019575f3b5dfbb789fa4952eb9646`](https://github.com/MLforHealth/S2SD/tree/1ef26e4e273019575f3b5dfbb789fa4952eb9646).
  The source has an [MIT license, copyright 2020 MLforHealth](https://github.com/MLforHealth/S2SD/blob/1ef26e4e273019575f3b5dfbb789fa4952eb9646/LICENSE).
- [R-Margin paper](https://arxiv.org/abs/2002.08473) and
  [Margin loss/distance-weighted sampling paper](https://arxiv.org/abs/1706.07567).

The upstream is pinned in `third_party/upstreams.toml`, fetched only through
`scripts/fetch_upstreams.py`, and marked reference-only. The new PyTorch
module is independently written from the equations and explicit audited
conventions; no upstream implementation is imported, copied or redistributed.
Audited source files are `criteria/{s2sd,margin}.py`,
`batchminer/{rho_distance,distance}.py`, `architectures/resnet50.py`,
`parameters.py`, `main.py`, and `Sample_Runs/Sample_Runs.sh`.

## Architecture and objective

The student is the shared MotionBERT action head: temporal mean, flattened
joint features, person mean, linear projection to 512, L2 normalization.
Only this student produces retrieval embeddings. Its head initialization,
physical batches and seed remain paired with other common-head methods.

The four teachers have output dimensions **512, 1024, 1536 and 2048**.
Each has an independent `Linear(8704,d) → ReLU → Linear(d,d) → L2` branch.
The official sample recipe retains the 512 teacher even for a 512 student.
Each teacher and the student has its own trainable class boundary vector and
independent R-Margin sampling stream. All teacher metric losses train the
shared encoder. The frozen track leaves the encoder frozen and is supplemental.

For unit student rows `S` and teacher rows `T`, define

`D(S,T) = temperature² / batch_size × Σᵢ KL(softmax((TTᵀ)ᵢ/temperature) || softmax((SSᵀ)ᵢ/temperature))`.

All batch positions, **including self**, participate in each row softmax.
Only the target branch of this term is detached. Teacher metric losses retain
their full gradient. The direction is teacher-to-student KL, following the
official `kl_div(log_softmax(student), softmax(teacher.detach()))` operation.
The feature target is likewise detached. With four teachers, the objective is

`0.5 × (student_RMargin + mean(teacher_RMargin)) + 50 × mean(D(student,teacher)) + 50 × D(student,features)`.

The feature term is absent for the first **1,000 completed updates** and first
participates in update **1,001**. Temperature is 1. Development histories may
record earlier validations, but selection and final training must include
the feature term. A 1,000-step priority-pilot configuration cannot certify
this method. The full selection budget must reach at least 1,001 updates.

## R-Margin and source conventions

Each anchor normally draws one uniformly sampled other same-class positive
and one other-class negative using inverse hypersphere density:

`weight(d) ∝ d^(2-D) × (1-d²/4)^(-(D-3)/2)`.

Distances are floored at 0.5. The source's upper-distance cutoff is commented
out; this implementation also has **no upper cutoff**. Computation uses
detached float64 normalized vectors and log probabilities. The sphere term
is clamped only at float64 machine epsilon to define exact antipodes safely.
That is a numerical endpoint convention, not a candidate-selection cutoff.

With probability **0.4**, the triplet instead becomes
`(anchor, anchor, another same-class item)`, pushing a same-class pair apart.
This is the source's actual R-Margin random switch. Cars uses 0.35 and SOP
0.15; the declared motion recipe starts from CUB's 0.4.

For each sampled triplet, use
`relu(d_ap-beta[class]+0.2) + relu(beta[class]-d_an+0.2)`.
Pair distances include the source's `1e-8` under the square root. The five
boundary vectors initialize to 1.2; no beta regularizer is enabled.

The audited source divides the hinge sum by the number of triplets with at
least one active hinge. It adds boolean masks, which computes their union.
This is historical behavior, not an accidental modern-PyTorch reinterpretation:
the linked baseline declares PyTorch 1.2+, and the
[PyTorch 1.2 bool-add kernel](https://github.com/pytorch/pytorch/blob/v1.2.0/aten/src/ATen/native/cpu/BinaryOpsKernel.cpp)
already returns a bool for bool addition. The paper does not specify a
different active-pair divisor. An analytical both-hinges-active test fixes
this convention explicitly; replacing the divisor with two would halve that
case's loss. If no hinge is active the loss is zero.

## Declared motion and runtime changes

1. **Feature aggregation:** image spatial mean+max becomes temporal/person
   mean+max **per joint**, flattened in joint/channel order. Mean and max
   are summed, not concatenated. Confidence-positive input tokens determine
   validity; absent people and padded tokens contribute to neither operation.
   All-invalid joints produce zero. Teachers receive 17×512 = 8704 features,
   replacing the ResNet's 2048 features. The common student pooling is retained.
2. **Optimizer:** teachers use the common motion AdamW learning rate/decay.
   The five beta vectors use the paper's **5e-4** learning rate and zero decay.
   The official S2SD wrapper assigns criterion parameters the common learning
   rate even though Margin exposes its own beta rate; this adapter follows
   the paper's declared beta rate. Shared encoder optimization and selection
   follow the preregistered motion budget, rather than image epochs.
3. **Sampling state:** each branch uses a private CPU Torch RNG initialized
   from the run seed, with distinct streams. This preserves the sampling law,
   not the upstream NumPy draw sequence. It prevents architecture-specific
   sampling from changing the shared model's dropout RNG stream. Five byte
   RNG states and the completed-update counter are persistent buffers.
4. **Checkpoints:** model, teacher MLPs, five boundaries, five sampler states,
   counter, and optimizer state must be retained. Runtime checks verify state
   shape, valid sampler bytes and a counter equal to the selected update plus the declared profile offset.
   Saving/restoring the optimizer is required to resume Adam moments exactly.
   Evaluation loads only the student's model state for cosine retrieval.

The teacher MLPs add **52,439,040 parameters**, before the five class boundary
vectors. Their float32 parameters, gradients and two Adam moments alone use
about 800 MiB. Profile the complete physical 32-example MotionBERT update,
all four teacher losses, optimizer state, and activated feature-distillation
term on the allocated GPU before fixing the run budget. Record actual peak
allocated/reserved memory, step time and checkpoint size. Do not shrink
teacher dimensions or replace physical batches to make a run fit silently.

## Verification evidence

`tests/unit/test_benchmark_s2sd.py` uses synthetic inputs to check inverse
density, exact switching semantics, both-active normalization, beta gradients,
teacher-to-student KL and stopped gradients, masked mean+max, delayed activation,
all teacher updates, single encoder pass, frozen/fine-tuned behavior, student
inference independence, and exact checkpoint/optimizer continuation. These
checks do not read motion data or authorize novel-test opening. Existing
complete-roster, six-seed and immutable test-opening requirements still apply.

### Capacity-profile convention

Profiles initialize the feature-delay counter at 1,000 and execute real complete
updates with feature distillation active. The immutable recipe records the offset
and `post_feature_delay_capacity`; this does not claim 1,000 trained updates.
Scientific development/final runs start at zero. Named AdamW groups, learning
rates, decay, exact parameter membership, moment shapes and actual optimizer
update counts are independently validated on load.
