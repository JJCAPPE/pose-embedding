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
- `scripts/download_arxiv_pdfs.sh`: downloads arXiv PDFs into `pdfs/` when run on a machine with internet access.
- `scripts/clone_repositories.sh`: clones the referenced public GitHub repositories into `repos/`.
- `project_brief/kulis_contextual_motion_research_brief.md`: the uploaded project brief used as context.

## Important note

The execution environment used to generate this archive could not resolve external hosts for direct PDF downloads, so PDFs themselves are not embedded. Instead, this archive includes stable abstract-page URLs, direct PDF URLs, and downloader scripts. This avoids silently creating an incomplete PDF bundle.

## Suggested use

From the extracted ZIP root:

```bash
bash scripts/download_arxiv_pdfs.sh
bash scripts/clone_repositories.sh
```

This will produce local `pdfs/` and `repos/` directories.
