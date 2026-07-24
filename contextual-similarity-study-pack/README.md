# Contextual Similarity Study Pack

Prepared for the final-proposal discussion on robust pose-sequence retrieval with contextual metric learning.

## Contents

- `contextual_similarity_textbook.pdf` — original compiled 45-page mathematical and implementation guide.
- `contextual_similarity_textbook_beginner_first.pdf` — expanded 76-page beginner-first edition. It introduces every symbol and prerequisite concept before developing the foundation paper's formal equations, proofs, implementation, and pose-retrieval adaptation.
- `contextual_similarity_meeting_brief.pdf` — compiled two-page discussion reference.
- `contextual_loss_reference.py` — tested PyTorch reference implementation of the contextual objective.
- `contextual_similarity_textbook.tex` — complete LaTeX source for the original textbook.
- `contextual_similarity_textbook_beginner_first.tex` — complete LaTeX source for the expanded beginner-first textbook.
- `contextual_similarity_meeting_brief.tex` — complete LaTeX source for the meeting brief.
- `contextual_similarity_study_pack.zip` — archive containing the original complete pack.

## Recommended reading order

1. Start with `contextual_similarity_textbook_beginner_first.pdf` when notation, vector geometry, indicator functions, gradients, or the contextual-similarity equations are not yet automatic.
2. Read the two-page meeting brief immediately before the discussion.
3. Review the textbook's executive roadmap, five-equation core, ranking proposition, and worked eight-sample example.
4. Use the implementation and experiment chapters when discussing feasibility and experimental controls.
5. Keep the discussion script and cheat sheet open during the meeting.

## Compile the LaTeX sources

From this directory:

```bash
latexmk -pdf contextual_similarity_textbook.tex
latexmk -pdf contextual_similarity_textbook_beginner_first.tex
latexmk -pdf contextual_similarity_meeting_brief.tex
```

The sources use standard TeX Live packages, including TikZ, PGFPlots, `tcolorbox`, and `listings`.

## Run the implementation smoke test

```bash
python contextual_loss_reference.py
```

The script validates batch balance, computes contextual similarity and the full hybrid loss, runs back-propagation, and checks that outputs and gradients are finite. PyTorch is required.
