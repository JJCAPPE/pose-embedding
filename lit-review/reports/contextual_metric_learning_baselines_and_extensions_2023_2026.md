# Contextual Metric Learning Baselines and Post-2023 Extensions

Research note for extending the pose-embedding proposal. Sources were checked through **31 July 2026**. “Optimization” is interpreted here as a metric-learning **objective and its required training procedure** (loss, miner, proxy parameters, queue, or outer loop), not as the choice between Adam and SGD.

## Executive conclusion

The page supplied by the user is from Liao, Tsiligkaridis, and Kulis, **“Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization,” ICML 2023** ([PMLR paper](https://proceedings.mlr.press/v202/liao23b.html), [final PDF](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf), [official code](https://github.com/Chris210634/metric-learning-using-contextual-similarity)).

The clean first extension is not to put every row visible in the screenshot into one supposedly controlled table. Many rows are results copied from papers whose architectures or training tricks differ. The 2023 authors' **controlled, rerun main-table comparator suite** comprises:

1. Contrastive loss
2. Triplet loss with distance-weighted mining
3. Multi-Similarity (MS) loss without a miner
4. Multi-Similarity loss with its miner
5. Proxy Anchor
6. Proxy NCA
7. ROADMAP

The appendix broadens the rerun set with **NT-Xent, Fast-AP, and Smooth-AP**. Appendix analyses also study **Softbin-AP and Blackbox-AP**, although Blackbox-AP is absent from the released repository and Softbin-AP is not wired into its command-line training path. A literal “all algorithms shown” study remains possible, but should be a second, explicitly architecture/framework-transfer tier.

For the proposed pose domain, this suite should be reproduced with one fixed pose encoder and evaluation pipeline. The strongest additions after 2023 are:

- **Stop-Gradient Softmax Loss (SGSL, AAAI 2023)** as a small, feasible classification/proxy-family addition;
- **Mean-Field Contrastive and Mean-Field Class-Wise Multi-Similarity (ICLR 2024)** as efficient class-wise counterparts to pair losses;
- **Potential Field Metric Learning (PFML, CVPR 2025)** as the most conceptually interesting recent comparator to contextual neighborhood reasoning;
- **Neural-Collapse-Informed Initialization with Perturbation Injection (AAAI 2026)** as a current proxy-training watchlist method;
- the older but directly relevant **continuous-label metric-learning objective for human pose retrieval (CVPR 2019)**, because pose similarity is often graded rather than binary.

Recent motion/pose retrieval papers mostly change modalities, encoders, or data rather than proposing drop-in pose-to-pose losses. They belong in a separate extension, not in the controlled loss table.

## 1. What the 2023 paper actually compared

### 1.1 Controlled main-table suite

Tables 2 and 3 use a dagger to mark results rerun by Liao et al. under their setup. The official repository confirms the exact implementations at commit [`8433dcb`](https://github.com/Chris210634/metric-learning-using-contextual-similarity/tree/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d):

| Family | Baseline to reproduce | Exact 2023 variant | Why it belongs |
|---|---|---|---|
| Pairwise | Contrastive | Local cosine-margin loss; positive margin 0.9, negative margin 0.6 ([code](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L178-L193)) | Canonical pairwise reference |
| Tuple + mining | Triplet | `TripletMarginLoss(margin=0.05)` with `DistanceWeightedMiner`; the miner is part of the method ([code](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L270-L281)) | Canonical relative-ranking reference |
| Pair ranking | Multi-Similarity | PyTorch Metric Learning MS loss, no miner ([code](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L98-L105)) | Separates the objective from mining |
| Pair ranking + mining | MS + miner | MS loss with `MultiSimilarityMiner` ([code](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L107-L115)) | Tests the value of informative-pair selection |
| Proxy | Proxy Anchor | One learned proxy per class; local implementation ([code](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L28-L60)) | Strong proxy-based family |
| Proxy | Proxy NCA | PyTorch Metric Learning Proxy NCA with scale 9 in the 224-pixel code ([code](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L86-L96)) | Classification-like metric reference |
| Listwise AP | ROADMAP | Supervised AP surrogate mixed 50/50 with the local contrastive loss ([code](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L225-L238)) | Directly optimizes ranking quality |

The contextual method itself is not a single isolated loss term. The released training objective combines contextual loss, contrastive loss, and an average-similarity regularizer ([224-pixel hybrid](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/losses.py#L240-L255), [regularizer application](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/train.py#L299-L305)). The proposal should therefore call it the **full contextual training objective** and include ablations of its contextual, contrastive, and regularization components.

### 1.2 Appendix suite

Appendix Table 4 uses 256-pixel inputs and 512-dimensional embeddings. Here the dagger convention is reversed: daggered N-Softmax and Proxy NCA++ values are copied from their original papers; the unmarked methods were rerun. The extra controlled baselines are:

- **NT-Xent**
- **Fast-AP**
- **Smooth-AP**

The released trainer exposes these alongside Contrastive, Triplet, MS, ROADMAP, and Contextual ([criterion setup](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/main.py#L114-L120), [loss dispatch](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/main.py#L252-L275)).

For literal completeness, **Normalized Softmax** ([source paper](https://arxiv.org/abs/1811.12649)) and **ProxyNCA++** ([ECCV paper](https://www.ecva.net/papers/eccv_2020/papers_ECCV/html/4637_ECCV_2020_paper.php)) can be added after the controlled appendix suite. They should be labelled as newly implemented pose transfers, not as 2023 author reproductions. ProxyNCA++ also combines an objective change with low-temperature scaling, global max pooling, and fast-moving proxies; its loss-only and full-recipe forms should be separated.

Appendix I.6 additionally evaluates convex combinations of contrastive loss with **Softbin-AP** and **Blackbox-AP**. These are useful completeness targets, but they are implementation work rather than simple configuration changes: Softbin-AP code is present but not connected to the 224-pixel loss dispatcher, and Blackbox-AP is not in the official repository.

### 1.3 Copied rows and how they could map to pose

DRML, DIML, DiVA, IBC, S2SD, the Metrix combinations, HIST, MHGL, PA+AVSL, and the first published-result rows for MS and Proxy Anchor were copied from their source papers. They incorporate different architectures, aggregation, distillation, regularization, embedding sizes, or other training changes. Reproducing them would answer a second question—**which broader image-retrieval mechanisms transfer to pose?**—rather than the controlled objective question.

| Copied method | Mechanism in its source paper | Plausible pose-domain mapping | Scope/priority |
|---|---|---|---|
| **DRML** ([ICCV 2021](https://openaccess.thecvf.com/content/ICCV2021/html/Zheng_Deep_Relational_Metric_Learning_ICCV_2021_paper.html)) | Learns an ensemble of aspect features, builds a graph between them, and performs relational inference | Let sub-embeddings specialize in body parts, kinematic factors, viewpoints, or temporal scales | Architecture-level; medium priority |
| **DIML** ([ICCV 2021](https://openaccess.thecvf.com/content/ICCV2021/html/Zhao_Towards_Interpretable_Deep_Metric_Learning_With_Structural_Matching_ICCV_2021_paper.html)) | Computes an optimal matching flow between spatial feature maps and decomposes similarity into part-wise contributions | Match joint, limb, or temporal tokens rather than CNN spatial cells | Scientifically attractive, but changes the pairwise similarity function and retrieval cost |
| **DiVA** ([ECCV 2020](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123530579.pdf)) | Aggregates complementary representations learned from several self-supervised/metric tasks | Assign auxiliary tasks to view, local articulation, global action, or temporal variation | Multi-head/task architecture; medium–low priority |
| **IBC** ([ICML 2021](https://proceedings.mlr.press/v139/seidenschwarz21a.html)) | Refines all mini-batch embeddings through attention-weighted message passing | Apply the same batch graph to pose embeddings | High scientific priority: it is a close architectural comparator to contextual batch-neighborhood reasoning |
| **S2SD** ([ICML 2021](https://proceedings.mlr.press/v139/roth21a.html)) | Distils similarity from auxiliary high-dimensional embedding and feature spaces into a compact retrieval embedding | Add training-only high-dimensional pose heads and retain the compact pose vector at test time | High feasibility; preserves inference cost |
| **Metrix** ([ICLR 2022](https://arxiv.org/abs/2106.04990)) | Generalizes mixup to metric pairs and applies it to Contrastive, MS, and Proxy Anchor | Prefer feature/embedding mixup; naïve coordinate interpolation may create anatomically invalid poses | High feasibility as an augmentation wrapper; test validity of mixed poses |
| **HIST** ([CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Lim_Hypergraph-Induced_Semantic_Tuplet_Loss_for_Deep_Metric_Learning_CVPR_2022_paper.html)) | Builds class-specific semantic tuplets and a hypergraph neural-network classification loss | Treat batch poses as nodes and pose classes/prototypes as hyperedges | High scientific priority, especially for the planned corruption study; adds an HGNN and prototype distributions |
| **MHGL** ([WACV 2022](https://openaccess.thecvf.com/content/WACV2022/papers/Ebrahimpour_Multi-Head_Deep_Metric_Learning_Using_Global_and_Local_Representations_WACV_2022_paper.pdf)) | Combines local/global features, pairwise/proxy losses, and second-order attention | Combine global sequence descriptors with joint- or segment-level descriptors | Architecture-heavy; low priority for a loss-focused thesis |
| **PA + AVSL** ([CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Zhang_Attributable_Visual_Similarity_Learning_CVPR_2022_paper.html)) | Represents pair similarity as a semantic hierarchy graph and performs bottom-up construction/top-down correction | Use the anatomical joint–limb–body hierarchy or temporal hierarchy | Potentially interpretable, but pair-dependent and a substantial departure from single-vector retrieval |

If the proposal promises the literal full transfer, the most defensible order is **IBC, S2SD, Metrix, and HIST first**, followed by the more architecture-specific DRML, DIML, DiVA, MHGL, and AVSL systems. Published MS and Proxy Anchor rows are duplicates of objectives already in the controlled suite, not additional algorithms.

This distinction and phased commitment should be explicit in both proposal versions; otherwise “all algorithms” creates a much larger project than “all controlled loss baselines.”

## 2. What “same encoder” must mean

The original main comparison used a pretrained ResNet-50, GeM pooling, a linear retrieval embedding, L2 normalization, and frozen batch normalization ([encoder](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/net/resnet.py#L22-L92)). CUB and Cars also commonly used a training-only projector that was discarded at retrieval time, whereas SOP used an identity projector ([training/evaluation path](https://github.com/Chris210634/metric-learning-using-contextual-similarity/blob/8433dcb67c2205c0e30ec07ed1e5b2fb92da016d/224x224/train.py#L299-L337)).

For the pose study, hold the following fixed unless the method logically requires an extra component:

- pose encoder, initialization/checkpoint, pooling, projection head, embedding dimension, normalization, and input representation;
- train/validation/test identities and retrieval gallery/query construction;
- data augmentation and pose-corruption protocol;
- optimizer, learning-rate search space, schedule, epoch or update budget, and checkpoint-selection rule;
- batch size and class/instance composition;
- number of seeds and hyperparameter-search budget;
- evaluation metrics and distance function.

Then report unavoidable method-specific state explicitly:

- **miners** for Triplet and MS;
- **class proxies/classifier weights** for Proxy NCA, Proxy Anchor, SGSL, mean-field methods, and PFML;
- **queues and momentum encoders** for SimPLE;
- **outer optimization loops** for chance-constrained proxy learning.

Two complementary comparisons are defensible:

1. **Strict-control track:** identical training recipe wherever technically possible.
2. **Best-practice track:** equal tuning budget, allowing each objective its documented sampler/miner and learning rate.

The strict track isolates objective behavior; the best-practice track measures realistic attainable performance. Reporting only one can be misleading because proxy and batch-pair objectives have different sampling requirements.

The original table also mixes 512- and 1536-dimensional embeddings in its final rows. The pose proposal should not do that. Every primary result should use one fixed dimensionality; any dimension scaling study should be a separate ablation.

## 3. New general metric-learning candidates, 2023–2026

The ranking below favors objectives that can train the same pose encoder and excludes methods whose principal novelty is a new backbone.

| Priority | Method | What changes | Feasibility with a fixed pose encoder | Research value |
|---|---|---|---|---|
| Core modern | **SGSL** — Stop-Gradient Softmax Loss, AAAI 2023 ([paper](https://ojs.aaai.org/index.php/AAAI/article/view/25421), [DOI](https://doi.org/10.1609/aaai.v37i3.25421)) | Adds an L2-normalized proxy/classifier branch whose hard-negative softmax term stops gradients through class weights; trained with ordinary softmax | **High.** Small loss/head implementation; no miner. The paper's “remove last BN-ReLU” architecture change should be omitted in the controlled track or reported separately. No official code link was found. | Adds a recent classification/proxy perspective with little engineering risk |
| Core modern | **MFCont and MFCWMS** — Mean Field Theory in DML, ICLR 2024 ([paper](https://proceedings.iclr.cc/paper_files/paper/2024/hash/1e55c38dd7d465c2526ae29d7ec85861-Abstract-Conference.html), [PDF](https://proceedings.iclr.cc/paper_files/paper/2024/file/1e55c38dd7d465c2526ae29d7ec85861-Paper-Conference.pdf)) | Replaces sample-pair interactions with learned class mean fields derived from Contrastive and class-wise MS objectives | **High–medium.** Same encoder plus class parameters; no elaborate mining. No official code link was found. | Directly tests whether class-level fields transfer better than within-batch contextual neighborhoods |
| High-value stretch | **PFML** — Potential Field Based Deep Metric Learning, CVPR 2025 ([paper](https://openaccess.thecvf.com/content/CVPR2025/html/Bhatnagar_Potential_Field_Based_Deep_Metric_Learning_CVPR_2025_paper.html), [project](https://shubhangb97.github.io/potential_field_DML/)) | Models decaying attractive/repulsive influence among all samples in a batch and uses multiple proxies per class | **Medium.** Compatible with the same encoder but needs a new loss and proxy bank. No public code link was found on the paper/project pages. | The closest recent conceptual foil to contextual similarity: global within-batch geometry without tuple mining; the paper also studies label-noise robustness |
| Optional | **SimPLE**, ICCV 2023 ([paper](https://openaccess.thecvf.com/content/ICCV2023/html/Wen_Pairwise_Similarity_Learning_is_SimPLE_ICCV_2023_paper.html), [project](https://simple.is.tue.mpg.de/)) | A pairwise BCE-style similarity objective without angular margins or normalized proxies | **Medium.** Its reported system relies on a FIFO queue and moving-average encoder, so it is not a loss-only swap. The project points to the broader [OpenSphere](https://github.com/ydwen/opensphere) repository rather than a clearly isolated turnkey implementation. | Tests a deliberately simple pairwise formulation, but confounds must be disclosed |
| Optional framework | **Deep Metric Learning with Chance Constraints**, WACV 2024 ([paper](https://openaccess.thecvf.com/content/WACV2024/html/Gurbuz_Deep_Metric_Learning_With_Chance_Constraints_WACV_2024_paper.html), [code](https://github.com/yetigurbuz/ccp-dml)) | Iteratively projects embeddings into probabilistic class constraints and reinitializes multiple class proxies | **Medium–low.** Same backbone is possible, but an outer optimization loop and proxy-selection procedure are required. | Tests whether constraint satisfaction improves robustness beyond changing the loss |
| Optional framework | **DADA**, AAAI 2024 ([paper](https://ojs.aaai.org/index.php/AAAI/article/view/29400), [code](https://github.com/Noahsark/DADA)) | Data-augmented domain alignment layered onto proxy-based DML | **Medium–low.** A plug-in framework, not a standalone objective. | Useful only if the project explicitly studies train/test pose-domain shift |
| Optional framework | **Deep Disentangled Metric Learning**, AAAI 2025 ([paper](https://ojs.aaai.org/index.php/AAAI/article/view/34184), [DOI](https://doi.org/10.1609/aaai.v39i19.34184)) | Information-bottleneck-inspired class-agnostic regularization for proxy algorithms | **Medium–low.** Adds heads/regularization; no official code link was found. | Relevant if pose nuisance disentanglement becomes a primary question |
| Exploratory | **Weak-metric Cross-Entropy**, ACML/PMLR 2025 ([paper](https://proceedings.mlr.press/v260/mou25a.html)) | Extends Cross-Entropy into a weak metric used for both classification training and retrieval distance | **Medium technically, low evidentially.** Its reported study is on CIFAR-10/100 rather than standard unseen-class retrieval, and no official code was found. | A cheap exploratory classification-metric baseline, but not a core claim |
| 2026 watchlist | **NC-Init with Perturbation Injection**, AAAI 2026 ([paper](https://ojs.aaai.org/index.php/AAAI/article/view/37777), [DOI](https://doi.org/10.1609/aaai.v40i10.37777), [code](https://github.com/jinnnnnnnnn/NC_init_PI)) | Initializes the task classifier/proxy directions from neural-collapse directions in a pretrained classifier, then injects small isotropic Gaussian perturbations during fine-tuning | **Medium.** Public code exists, but it requires a compatible pretrained classifier and is an initialization/fine-tuning procedure rather than a loss swap. | The strongest verified 2026 watchlist item for the proxy/classification family; especially relevant if the pose encoder is pretrained |

NC-Init with Perturbation Injection is the one verified peer-reviewed 2026 addition that is sufficiently documented and method-relevant. It should remain a watchlist/secondary experiment because its causal question is pretraining geometry and proxy initialization, not contextual-versus-alternative loss design.

## 4. Pose- and motion-specific objectives

### 4.1 Directly comparable pose objective

**Deep Metric Learning Beyond Binary Supervision**, CVPR 2019 ([CVF paper](https://openaccess.thecvf.com/content_CVPR_2019/html/Kim_Deep_Metric_Learning_Beyond_Binary_Supervision_CVPR_2019_paper.html)), predates the requested window but should be a core domain control. It proposes ratio-preserving triplet learning and mining for **continuous similarity labels** and evaluates human pose retrieval. This matters because two poses can differ by a small, meaningful amount; forcing every pair into identical/different classes discards that geometry.

If the pose data has a continuous pose-distance or transition-distance target, include:

- the paper's continuous-label ratio/triplet objective;
- an ordinary binary-label Triplet objective on the same batches;
- contextual similarity trained from the chosen binary or graded neighborhood definition.

That comparison asks whether contextual neighborhood structure adds value beyond directly supervising graded pose distance.

### 4.2 Recent work that belongs in a separate extension

| Work | Objective contribution | Why it is not a primary same-encoder baseline | Suitable use |
|---|---|---|---|
| **TMR: Text-to-Motion Retrieval Using Contrastive 3D Human Motion Synthesis**, ICCV 2023 ([paper](https://openaccess.thecvf.com/content/ICCV2023/papers/Petrovich_TMR_Text-to-Motion_Retrieval_Using_Contrastive_3D_Human_Motion_Synthesis_ICCV_2023_paper.pdf), [code](https://github.com/Mathux/TMR)) | Cross-modal contrastive alignment plus motion reconstruction/generation | Requires paired language, text encoder, and generative branch | Optional text-to-motion transfer experiment |
| **Tri-Modal Motion Retrieval**, CVPR 2024 ([paper](https://openaccess.thecvf.com/content/CVPR2024/html/Yin_Tri-Modal_Motion_Retrieval_by_Learning_a_Joint_Embedding_Space_CVPR_2024_paper.html)) | Joint contrastive space for video, text, and 3D motion with reconstruction | Changes modalities and representation system | External whole-system reference |
| **CAR: Chronologically Accurate Retrieval**, ECCV 2024 ([paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/07570.pdf)) | Uses chronologically shuffled event descriptions as hard negatives | Motion-language temporal grounding, not pose-to-pose metric learning | Borrow its order-sensitive negative/evaluation idea for sequence retrieval |
| **PoseEmbroider**, ECCV 2024 ([paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08959.pdf)) | Multimodal pose/image/text representation trained with retrieval objectives | Transformer and multimodal architecture are central | Future multimodal representation extension |
| **PoseScript**, TPAMI 2025 ([DOI](https://doi.org/10.1109/TPAMI.2024.3407570), [preprint](https://arxiv.org/abs/2210.11795)) | Learns pose–text retrieval using automatically generated and human pose descriptions | Cross-modal single-pose task with an additional text encoder | Optional benchmark if semantic descriptions of poses are in scope |
| **Cross-Consistent Contrastive Loss / MoT++**, ACM TOMM 2025 ([DOI](https://doi.org/10.1145/3744565), [code](https://github.com/mesnico/MOTpp), [preprint](https://arxiv.org/abs/2407.02104)) | Adds unimodal consistency constraints to a text-motion common space and supports joint-dataset learning | Requires paired text-motion encoders and multiple datasets | Separate cross-modal or cross-dataset robustness experiment |
| **UniHPR: Unified Human Pose Representation via Singular Value Contrastive Learning**, IEEE MIPR 2025 ([DOI](https://doi.org/10.1109/MIPR67560.2025.00072), [preprint](https://arxiv.org/abs/2510.19078)) | Pairwise InfoNCE plus a singular-value Triplet-InfoNCE over aligned image, 2D-pose, and 3D-pose embeddings | Requires three paired modalities, multiple encoders, and very large batches | Strong optional extension if paired 2D/3D views exist |

These papers establish that recent pose/motion retrieval work emphasizes **cross-modal consistency, temporal ordering, and paired-view alignment**. The proposal can use those ideas to motivate later experiments, but putting their headline numbers beside a fixed-encoder pose-to-pose loss table would not be a controlled comparison.

## 5. Recommended experimental ladder

### Phase A — faithful 2023 transfer

Use one pose encoder and reproduce:

- Contrastive
- Triplet + distance-weighted miner
- MS without miner
- MS + miner
- Proxy Anchor
- Proxy NCA
- ROADMAP
- full Contextual objective

Verify each implementation first on a small deterministic split. Then run the clean and corrupted-pose protocols with identical retrieval metrics and multiple seeds.

### Phase B — complete the 2023 objective families

Add:

- NT-Xent
- Fast-AP
- Smooth-AP
- optionally Softbin-AP and Blackbox-AP if implementation time permits
- optionally Normalized Softmax and ProxyNCA++ as newly implemented transfers of the appendix's copied references

This phase separates pairwise, tuple/mining, proxy/classification, and direct-AP optimization families.

### Phase C — modern and domain-specific objectives

Recommended order:

1. continuous-label pose metric learning from CVPR 2019;
2. SGSL;
3. MFCont and MFCWMS;
4. PFML;
5. NC-Init with Perturbation Injection if the encoder is pretrained;
6. SimPLE only if the queue/momentum-encoder confound is acceptable.

Treat chance-constrained proxy learning, DADA, and disentangled proxy regularization as optional framework studies. Treat TMR, CAR, PoseEmbroider, CCCL/MoT++, and UniHPR as a separate multimodal/temporal work package.

### Phase D — full 2023 whole-system transfer, if resources permit

Implement the copied framework rows as explicitly non-loss-only studies. Prioritize IBC, S2SD, Metrix, and HIST; then consider DRML, DIML, DiVA, MHGL, and PA+AVSL. This phase satisfies the ambitious “map every algorithm into pose” goal without compromising the causal interpretation of Phases A–C.

## 6. Minimum reporting matrix

For every core method, report:

- clean retrieval: Recall@K and mAP;
- pose-estimation corruption: performance by corruption type and severity;
- missing-joint and missing-frame robustness;
- cross-view or cross-subject generalization where the dataset permits;
- mean and standard deviation over the same seeds;
- training cost, peak memory, and inference-time cost;
- sensitivity to batch composition and embedding dimension;
- method-specific parameter count, including proxies or auxiliary heads.

Use paired seeds and the same corruptions across losses. Compare not only the best score but also:

- performance drop from clean to corrupted data;
- area under the corruption-severity curve;
- ranking stability and nearest-neighbor consistency;
- whether gains remain when tuning budgets are equal.

## 7. Proposal-ready formulation

> After establishing the original contextual-similarity pipeline in the pose-embedding domain, the project will conduct a controlled objective-transfer study. Keeping the pose encoder, embedding dimensionality, data splits, training budget, and retrieval protocol fixed, it will compare the full contextual objective against the loss families rerun in Liao et al. (2023): Contrastive, Triplet with distance-weighted mining, Multi-Similarity with and without mining, Proxy Anchor, Proxy NCA, and ROADMAP. A second tier will add the appendix objectives NT-Xent, Fast-AP, and Smooth-AP. The study will then evaluate selected post-2023 objectives—SGSL, mean-field metric learning, PFML, and the 2026 NC-informed proxy initialization procedure—together with continuous-label pose metric learning, chosen for their complementarity and feasibility with the same encoder. The image-retrieval frameworks whose published results were copied by Liao et al. will form a separate whole-system transfer tier, and recent multimodal motion objectives will be treated as a further extension because they require paired text, video, 2D/3D views, or additional encoders.

The resulting research question is stronger than a simple “does contextual loss improve pose retrieval?” It becomes:

> **Which metric-learning objective families transfer most effectively from image retrieval to pose retrieval, and which retain their gains under pose-specific noise, incomplete observations, view changes, and graded pose similarity?**

That framing supports both an empirical contribution—a controlled cross-domain benchmark—and a scientific contribution—an analysis of when contextual, pairwise, proxy, listwise, class-field, and continuous-label supervision match the geometry of pose retrieval.
