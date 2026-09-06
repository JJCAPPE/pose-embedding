# Pose Embedding Literature Review Source Archive

Generated: 2026-07-04

This ZIP contains the source package for the pose embedding / contextual metric learning literature review.

## Contents

- `sources_manifest.csv` / `sources_manifest.json`: complete machine-readable source list.
- `grouped_reading_list.md`: human-readable grouped reading list.
- `arxiv_pdf_urls.txt`: direct PDF URLs for all arXiv papers included in the review package.
- `papers_url_files/`: one Markdown file per paper/source reference.
- `repositories_url_files/`: one Markdown file per public code repository.
- `dataset_and_profile_sources/`: dataset/profile/source links that are not papers.
- `bib/references_minimal.bib`: minimal BibTeX-style entries for arXiv papers.
- `scripts/download_arxiv_pdfs.sh`: downloads arXiv PDFs into the ignored `pdfs/` directory and verifies them against `pdfs.sha256`.
- `pdfs.sha256`: checksums for the literature snapshot used during the review.
- `third_party/upstreams.toml` at the repository root replaces the former repository-clone script with pinned upstream commits.
- `project_brief/kulis_contextual_motion_research_brief.md`: the uploaded project brief used as context.

## Important note

PDFs and upstream repositories are intentionally not tracked in Git. The archive instead includes stable abstract-page URLs, direct PDF URLs, checksums, and reproducible fetch instructions. Existing local copies may remain in the ignored directories.

## Suggested use

From the extracted ZIP root:

```bash
bash scripts/download_arxiv_pdfs.sh
uv run python ../scripts/fetch_upstreams.py
```

This produces ignored local PDF and upstream-source caches without adding large third-party artifacts to the repository.
