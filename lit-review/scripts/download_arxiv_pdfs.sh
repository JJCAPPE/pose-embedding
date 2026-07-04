#!/usr/bin/env bash
set -euo pipefail
mkdir -p pdfs
while IFS= read -r line; do
  url="${line%%#*}"
  url="$(echo "$url" | xargs)"
  [ -z "$url" ] && continue
  id="$(basename "$url" .pdf)"
  echo "Downloading $id"
  curl -L --fail --retry 3 --retry-delay 3 -o "pdfs/${id}.pdf" "$url"
  sleep 1
 done < arxiv_pdf_urls.txt
