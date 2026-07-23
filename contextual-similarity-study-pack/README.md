# Contextual Similarity Study Pack

Prepared for the final-proposal discussion on robust pose-sequence retrieval with contextual metric learning.

## Contents

- `contextual_similarity_textbook.pdf` — compiled 45-page mathematical and implementation guide.
- `contextual_similarity_meeting_brief.pdf` — compiled two-page discussion reference.
- `contextual_loss_reference.py` — tested PyTorch reference implementation of the contextual objective.
- `contextual_similarity_textbook.tex` — complete LaTeX source for the textbook.
- `contextual_similarity_meeting_brief.tex` — complete LaTeX source for the meeting brief.
- `contextual_similarity_study_pack.zip` — archive containing the complete pack.

## Recommended reading order

1. Read the two-page meeting brief.
2. Review the textbook's executive roadmap, five-equation core, and worked eight-sample example.
3. Use the implementation and experiment chapters when discussing feasibility.
4. Keep the discussion script and cheat sheet open during the meeting.

## Compile the LaTeX sources

From this directory:

```bash
latexmk -pdf contextual_similarity_textbook.tex
latexmk -pdf contextual_similarity_meeting_brief.tex
```

The sources use standard TeX Live packages, including TikZ, PGFPlots, `tcolorbox`, and `listings`.

## Run the implementation smoke test

```bash
python contextual_loss_reference.py
```

The script validates batch balance, computes contextual similarity and the full hybrid loss, runs back-propagation, and checks that outputs and gradients are finite. PyTorch is required.
