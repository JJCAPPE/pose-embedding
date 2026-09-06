# Pinned upstream references

`upstreams.toml` replaces the repository's historical, unresolved gitlinks with
an explicit and auditable source manifest. Each checkout is created under the
ignored `.cache/upstreams/` directory by `scripts/fetch_upstreams.py`; upstream
repositories are never committed into this repository.

Run:

```bash
python scripts/fetch_upstreams.py
python scripts/fetch_upstreams.py --check
```

Use `--name MotionBERT` to fetch or verify one entry. The script refuses to
modify an existing checkout whose remote or HEAD differs from the manifest.

## License boundary

- MotionBERT is Apache-2.0 and is the only upstream expected to inform a small,
  attributed compatibility port for the frozen encoder.
- MotionCLIP and text-to-motion-retrieval are MIT licensed; MMAction2 is
  Apache-2.0; st-gcn is BSD-3-Clause. They remain reference-only because they
  are outside the locked experiment.
- The contextual-similarity repository has no visible license at the pinned
  revision. Treat it as **reference-only**: do not vendor, copy, adapt, or
  redistribute its code without written permission. Independently implement
  behavior from the paper and compare against the local audited reference.

The repository itself intentionally has no reuse license pending advisor and BU
review. Upstream licenses do not grant a license to this repository as a whole.
