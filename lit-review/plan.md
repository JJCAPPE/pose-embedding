The prompt below is designed for the exact archive and project framing we built: extending contextual metric learning from image retrieval to pose-sequence retrieval under pose-estimation noise. Your brief already frames the project as **metric learning / retrieval first**, with rowing/sports as a later application, and defines the core question as whether neighborhood-based contextual similarity improves robustness for noisy pose embeddings. Brian’s contextual-loss paper is the methodological anchor: it optimizes contextual similarity in addition to cosine similarity, reports robustness to label noise/overfitting, and provides public code.

Copy-paste this as the agent prompt.

```text
You are a technical research assistant preparing a concise literature review for Prof. Brian Kulis.

Context:
I am preparing an undergraduate research project tentatively titled:

“Robust Contextual Metric Learning for Pose-Based Human Motion Retrieval under Pose-Estimation Noise.”

The project goal is to study whether contextual metric learning, originally developed for image retrieval in “Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization” by Liao, Tsiligkaridis, and Kulis, can be adapted to human pose / skeleton sequence embeddings for motion retrieval. The key question is whether neighborhood-based contextual similarity improves retrieval robustness when pose inputs are noisy, incomplete, view-biased, jittery, or corrupted by pose-estimation errors.

You have access to:
1. A ZIP archive containing source cards, source manifests, paper links, repository links, dataset links, and scripts.
2. A set of downloaded PDFs, including but not limited to:
   - 2210.01908.pdf — Supervised Metric Learning to Rank for Retrieval via Contextual Similarity Optimization
   - 2003.08505.pdf — A Metric Learning Reality Check
   - 2008.09164.pdf — PyTorch Metric Learning
   - 2004.11362.pdf — Supervised Contrastive Learning
   - 1811.12649.pdf — Classification is a Strong Baseline for Deep Metric Learning
   - 1905.04757.pdf — NTU RGB+D 120
   - 1904.03278.pdf — AMASS
   - 2304.01865.pdf — SportsPose
   - 2211.15692.pdf — H3WB
   - 2004.06704.pdf — FineGym
   - 1212.0402.pdf — UCF101
   - 2206.13028.pdf — MST-GCN
   - 2010.07367.pdf — PR-GCN
   - 1905.06774.pdf / 2008.03791.pdf — RA-GCN / robust skeleton recognition
   - 2004.11085.pdf — SL-DML
   - 2012.13823.pdf — Skeleton-DML
   - 2106.09696.pdf — BABEL
   - 1607.03827.pdf — KIT Motion-Language Dataset
   - 2002.05907.pdf — Survey on 3D skeleton-based action recognition
   - 2401.08281.pdf — FAISS
3. A project brief file:
   - kulis_contextual_motion_research_brief.md

Your task:
Analyze the literature archive and write a concise but technically serious LaTeX literature review for Brian. The final report should explain the current state of the literature and what it means for the proposed project.

Primary questions the report must answer:
1. What has been done before us?
2. What existing datasets, architectures, losses, and retrieval protocols can we benchmark against?
3. Which public repositories or codebases can we build on?
4. How can we add contextual loss on top of existing pose/skeleton embedding code?
5. How feasible is this project, and what is the practical path to a first result?

Important constraints:
- Do not write a broad generic survey.
- Write specifically for this project.
- Distinguish clearly between:
  a. pose estimation datasets/models,
  b. skeleton-based action recognition,
  c. human motion representation learning,
  d. metric learning / retrieval,
  e. pose/motion retrieval under noisy inputs.
- Do not overclaim that prior work already solved our exact problem unless a paper explicitly does pose-sequence retrieval with metric learning and retrieval metrics.
- Be explicit about gaps: much work exists on skeleton action recognition and metric learning separately, but the intersection of contextual metric learning + pose-sequence retrieval + noise robustness appears underexplored.
- If a source does not provide public code, say so.
- If a dataset is not directly suited for retrieval, explain how it could still be converted into a retrieval benchmark.
- Prefer concrete implementation recommendations over abstract commentary.
- Every important factual claim must be cited with BibTeX references.
- Use only information available in the supplied PDFs, manifest files, source cards, and repository/dataset links. If you infer something, label it as an inference.

Expected output files:
1. `main.tex`
2. `references.bib`
3. optionally `README.md` with compile instructions

LaTeX requirements:
- Use standard article format.
- Target length: 5–8 pages excluding references.
- Use `\section{}`, `\subsection{}`, tables, and compact technical prose.
- Use `booktabs` for tables.
- Use `hyperref`.
- Use BibTeX or natbib-compatible citations.
- Include a clean title, author placeholder, and date.
- Title suggestion:
  “Literature Review: Pose-Based Motion Embeddings and Contextual Metric Learning for Robust Retrieval”
- Audience: Prof. Brian Kulis. Assume technical ML background. Do not over-explain basic ML, but define project-specific choices clearly.

Recommended report structure:

1. Abstract / Executive Summary
   - One paragraph.
   - State the main finding:
     Existing literature provides strong components—skeleton action recognition encoders, pose/motion datasets, metric-learning baselines, and contextual metric-learning code—but there appears to be an open opportunity to combine them for robust pose-sequence retrieval under pose-estimation noise.

2. Project Motivation and Research Question
   - Explain the proposed project in 2–3 paragraphs.
   - Frame it as retrieval / metric learning, not simply action classification.
   - Include this pipeline:
     pose sequence -> temporal/skeleton encoder -> fixed-length embedding -> nearest-neighbor retrieval -> retrieval metrics under clean/noisy conditions.
   - Explain why pose-estimation noise matters:
     joint jitter, missing joints, camera/viewpoint effects, occlusion, temporal jitter, 2D-to-3D lifting error.

3. Background: Contextual Metric Learning
   - Summarize Liao, Tsiligkaridis, and Kulis.
   - Explain:
     - image retrieval setting,
     - pairwise ranking vs classification losses,
     - contextual similarity as neighborhood overlap,
     - contextual loss + contrastive loss + similarity regularizer,
     - robustness to label noise / overfitting,
     - public code availability.
   - Explain why the loss is architecture-agnostic: it operates on embeddings and labels, so it can in principle be applied to pose-sequence embeddings.
   - Mention implementation requirements:
     - L2-normalized embeddings,
     - cosine similarity matrix,
     - balanced batch sampler with multiple samples per class,
     - k tied to samples per class,
     - contextual similarity computed within batch.

4. What Has Been Done Before: Literature Taxonomy
   Organize the literature into categories:
   a. General deep metric learning and retrieval
      - contrastive, triplet, multi-similarity, AP surrogates, supervised contrastive, classification/proxy baselines.
      - cite Metric Learning Reality Check, Supervised Contrastive Learning, Classification is a Strong Baseline, PyTorch Metric Learning.
   b. Skeleton-based action recognition
      - ST-GCN family, MST-GCN, transformers, PoseC3D-style representations if present in archive.
      - explain that these usually optimize classification accuracy, not retrieval quality.
   c. Robust skeleton recognition under noisy/incomplete poses
      - RA-GCN, PR-GCN, incomplete skeleton / jitter / occlusion papers.
      - explain relevance to our noise benchmark.
   d. Motion representation / mocap datasets
      - AMASS, BABEL, KIT Motion-Language.
      - explain potential for semantic retrieval or motion-language retrieval, but note added complexity.
   e. Direct metric learning for skeleton/action retrieval
      - Skeleton-DML, SL-DML.
      - emphasize these as especially relevant baselines because they explicitly frame action recognition as nearest-neighbor search in embedding space.
   f. Datasets for pose and action benchmarks
      - NTU RGB+D 120, SportsPose, FineGym, UCF101, H3WB, AMASS/BABEL.
      - classify each by modality, labels, scale, and suitability.

5. Dataset Benchmarking Options
   Create a table with columns:
   - Dataset
   - Modality
   - Scale
   - Labels / retrieval target
   - Strengths
   - Weaknesses
   - Suitability for first benchmark

   Required discussion:
   - NTU RGB+D 120 should likely be the first benchmark because it has large-scale skeletons, action labels, cross-subject/cross-setup splits, and one-shot/retrieval relevance.
   - SportsPose is valuable for sports relevance and dynamic 3D movements, but may be less directly suited to large-scale class retrieval depending on labels.
   - AMASS + BABEL is attractive for clean mocap + semantic labels, but preprocessing and label structure are more complex.
   - FineGym is good for fine-grained sports motion, but likely requires pose extraction from video unless preprocessed pose features are available.
   - UCF101 is useful only as a later raw-video-to-pose robustness extension, not the first project foundation.
   - H3WB is more useful for pose-estimation / whole-body robustness than direct motion retrieval.

6. Architecture Benchmarking Options
   Create a table with columns:
   - Architecture / codebase
   - Input format
   - Original task
   - Output embedding availability
   - Ease of adding contextual loss
   - Expected implementation difficulty

   Include:
   - simple TCN / GRU / LSTM baseline,
   - ST-GCN / MST-GCN,
   - Skeleton-DML / SL-DML,
   - PR-GCN / RA-GCN if code is available,
   - PyTorch Metric Learning as a loss/evaluation library,
   - Kulis contextual-loss repository as the source for contextual loss implementation.

   Explain:
   - The easiest first implementation is to take a skeleton/action model, replace or expose the penultimate feature as an embedding, L2-normalize it, and train with SupCon/triplet/contextual loss.
   - Skeleton-DML or SL-DML may be the most directly relevant existing baseline because they already formulate action recognition as nearest-neighbor retrieval in embedding space.
   - ST-GCN/MST-GCN are stronger skeleton encoders but may require adapting classification code to metric-learning training.

7. Losses and Evaluation Metrics
   Discuss losses:
   - cross-entropy classification baseline using penultimate layer as embedding,
   - contrastive loss,
   - triplet margin loss,
   - supervised contrastive loss,
   - multi-similarity loss,
   - contextual loss from Liao/Kulis,
   - hybrid contextual + contrastive loss.

   Discuss evaluation:
   - Recall@1, Recall@5, Recall@10,
   - mAP,
   - mAP@R if appropriate,
   - optional NDCG if using hierarchical/fine-grained labels,
   - cross-subject retrieval,
   - cross-view or cross-setup retrieval,
   - robustness degradation curves under noise.

   Emphasize:
   Classification accuracy is not sufficient. The proposed project should evaluate retrieval ranking quality.

8. Proposed Experimental Design
   Provide a concrete first experiment:
   - Dataset: NTU RGB+D 120 skeletons.
   - Task: action-class retrieval.
   - Splits: cross-subject and/or cross-setup.
   - Encoders:
     1. simple TCN baseline,
     2. adapted Skeleton-DML or ST-GCN/MST-GCN baseline.
   - Losses:
     1. cross-entropy embedding baseline,
     2. triplet,
     3. supervised contrastive,
     4. contextual loss,
     5. contextual + contrastive hybrid.
   - Noise corruptions:
     - Gaussian joint jitter,
     - random joint dropout,
     - limb dropout,
     - temporal jitter,
     - frame dropout,
     - scaling/rotation/view perturbations,
     - left-right swap if appropriate.
   - Metrics:
     - clean Recall@K/mAP,
     - noisy Recall@K/mAP,
     - robustness drop = clean score - noisy score,
     - optionally area under robustness curve.

9. How to Build on Existing Code
   Give a concrete process:
   Step 1: Reproduce Kulis contextual loss on a small image benchmark or at least inspect/run the loss implementation.
   Step 2: Reproduce a skeleton metric-learning baseline, preferably Skeleton-DML/SL-DML or a simple NTU skeleton encoder.
   Step 3: Refactor the model so training returns `embeddings, labels`.
   Step 4: Add balanced batch sampler: N classes x M examples per class.
   Step 5: Add losses from PyTorch Metric Learning and the contextual loss.
   Step 6: Add retrieval evaluator using brute-force cosine similarity first; FAISS only later if scale requires it.
   Step 7: Add noise-corruption module.
   Step 8: Run ablations.

   Include pseudocode in LaTeX:
```

z = normalize(encoder(x))
S = z z^T
Y_ij = 1[y_i = y_j]
W = contextual_similarity(S, k=M)
L = L_context(W, Y) + lambda \* L_contrastive(z, y)

```

10. Feasibility Assessment
Include a short feasibility table:
- Low-risk path:
  NTU RGB+D 120 + simple encoder + contextual loss + synthetic noise.
- Medium-risk path:
  ST-GCN/MST-GCN adaptation + full retrieval evaluation.
- Higher-risk path:
  SportsPose / FineGym / real video-to-pose pipeline.
- Highest-risk path:
  rowing-specific dataset or cross-dataset transfer.

Discuss compute:
- skeleton data is much lighter than raw video,
- first baselines can run on a subset,
- full NTU training likely needs one GPU,
- contextual loss requires sufficiently large balanced batches,
- use mixed precision / shorter sequence length / gradient accumulation if needed.

11. Main Literature Gap and Project Contribution
Clearly state the gap:
- Prior work has strong metric learning for images.
- Prior work has strong skeleton action recognition.
- Prior work has some skeleton/action metric learning for one-shot recognition.
- Prior work has robustness work for incomplete/noisy skeletons.
- But there appears to be room for a focused study of contextual metric learning for pose-sequence retrieval under controlled pose-estimation noise.

State the contribution:
- Adapt contextual loss to temporal pose embeddings.
- Benchmark against standard metric-learning and skeleton baselines.
- Evaluate not only clean retrieval but robustness curves under pose corruption.
- Provide a reproducible implementation using public datasets and code.

12. Recommended Plan for Brian
End with a concise recommendation:
- Start with NTU RGB+D 120.
- Use Skeleton-DML/SL-DML or a simple TCN as first baseline.
- Add SupCon/triplet/PyTorch Metric Learning baselines.
- Integrate Kulis contextual loss.
- Evaluate Recall@K/mAP under clean and noisy skeleton inputs.
- Add SportsPose only after the first benchmark works.
- Keep rowing as later demonstration, not as the first benchmark.

Required tables:
1. Literature taxonomy table.
2. Dataset comparison table.
3. Codebase / baseline table.
4. Proposed experimental matrix.
5. Feasibility and risk table.

Required final conclusion:
The report must end by directly answering:
- What has been done before us?
- What can we benchmark on?
- How can we build on existing code?
- Is the project feasible, and what is the first concrete path?

Bibliography instructions:
- Create `references.bib`.
- Include all cited papers and repositories/datasets where possible.
- Use stable BibTeX keys such as:
- liao2023contextual
- musgrave2020reality
- musgrave2020pml
- khosla2020supcon
- zhai2019classification
- liu2019ntu120
- mahmood2019amass
- ingwersen2023sportspose
- zhu2023h3wb
- shao2020finegym
- soomro2012ucf101
- chen2022mstgcn
- li2021prgcn
- song2020ragcn
- memmesheimer2021skeletondml
- memmesheimer2020sldml
- punnakkal2021babel
- plappert2016kit
- ren2024skeletonsurvey
- douze2025faiss

Quality bar:
- The report should read like a concise internal research memo, not a class essay.
- Prefer precise claims over exhaustive coverage.
- Every section should explain why the literature matters for our project.
- Do not include filler.
- Do not invent experimental results.
- Where the literature is ambiguous, say what is known, what is not known, and what we should test.
```
