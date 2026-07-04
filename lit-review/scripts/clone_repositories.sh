#!/usr/bin/env bash
set -euo pipefail
mkdir -p repos
cd repos
git clone https://github.com/Chris210634/metric-learning-using-contextual-similarity || true  # metric-learning-using-contextual-similarity
git clone https://github.com/Walter0807/MotionBERT || true  # MotionBERT
git clone https://github.com/GuyTevet/MotionCLIP || true  # MotionCLIP
git clone https://github.com/google-research/google-research/tree/master/poem || true  # POEM / Pr-VIPE
git clone https://github.com/open-mmlab/mmaction2 || true  # MMAction2
git clone https://github.com/yysijie/st-gcn || true  # ST-GCN PyTorch
git clone https://github.com/mesnico/text-to-motion-retrieval || true  # text-to-motion-retrieval
