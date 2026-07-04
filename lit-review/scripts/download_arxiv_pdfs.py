#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlretrieve
import time

root = Path(__file__).resolve().parents[1]
out = root / 'pdfs'
out.mkdir(exist_ok=True)
for raw in (root / 'arxiv_pdf_urls.txt').read_text().splitlines():
    url = raw.split('#', 1)[0].strip()
    if not url:
        continue
    arxiv_id = url.rstrip('/').split('/')[-1].replace('.pdf', '')
    dst = out / f'{arxiv_id}.pdf'
    print(f'Downloading {arxiv_id} -> {dst}')
    try:
        urlretrieve(url, dst)
    except Exception as e:
        print(f'FAILED {url}: {e}')
    time.sleep(1)
