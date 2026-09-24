# NTU RGB+D 120 manifest audit v2

Status: **adopted and independently regenerated**. This is the public-safe
release evidence for the [result-blind input-contract amendment](input-contract-amendment.v1.md).
The [v1 audit](ntu-manifest-audit.v1.md) is retained unchanged as the
pre-amendment historical snapshot, including its per-class table and all 40
named synchronized-view exclusions. The novel test remains sealed.

## Source accounting

- Usable HRNet aggregate annotations: **113,945** unique canonical IDs.
- Official missing-skeleton list: **535** unique canonical IDs, zero overlap
  with the aggregate.
- Nominal captures accounted for: **114,480**.
- All 120 actions and all 20 official one-shot exemplars are present.
- Physical sources: **2**, with exact relative paths, byte counts, and SHA-256
  digests bound by the amended protocol and listed in the
  [decision record](input-contract-amendment.v1.md).
- Current canonical protocol SHA-256:
  `c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.

## Immutable inventory and seven split manifests

All eight JSONL files in the fresh SCC bundle are byte-for-byte identical to
the prior verified release. The counts and SHA-256 digests are therefore the
same; they describe identities and partition membership, not retrieval
outcomes.

| JSONL file | Rows | Classes | SHA-256 |
| --- | ---: | ---: | --- |
| `source-inventory.jsonl` | 113,945 | 120 | `e0ab842fe2a62b50ff7205d0f8658fad373a03c5b29527c281a2db0225ea0058` |
| `development-train.jsonl` | 76,013 | 80 | `2278b58090dbd3a00255936c8e4a2bd40887af995a88672334e4ed296605661c` |
| `development-validation.jsonl` | 18,988 | 20 | `339f330d21e8a4bb712585d8c4074adac0adfad253c9046d3a397451f2f69b15` |
| `final-train.jsonl` | 95,001 | 100 | `5775b0b05dd2c80504433273d620069c64804a705a8f373a217e318c4aa28622` |
| `official-novel.jsonl` | 18,944 | 20 | `44a0da454a930530e56a6a398ede145cc6f8f0258403c01df7676305c143ba1c` |
| `novel-anchor.jsonl` | 20 | 20 | `176cd1715bfdff30613381834b90c7e0aba434648780e0ea435f2ccaab440d30` |
| `novel-query-primary.jsonl` | 18,884 | 20 | `c401ee11b3b0965ce46c3fb06e30eaa4859efbc8eb74931273ad793f77d9b4b9` |
| `novel-query-official.jsonl` | 18,924 | 20 | `cf74650e6c0d5fda31d4a3dc59fcd3825ca0b8f166e1963d85ac449d525412e9` |

The primary query excludes exactly 40 synchronized camera mates of the 20
anchors. The full per-class counts and exclusion identities in the v1 audit
remain valid because all eight JSONL inputs are byte-identical.

## Independent SCC verification

Grid Engine job `7721684` completed at `2026-09-24T16:32:58Z` with
`failed=0` and `exit_status=0` on commit
`7306af8ea73212d8c732e8577c04d9ecae747b49`. It verified the amended
protocol hash, protected physical-source SHA256SUMS, workspace and upstream
checks, Ruff, and all 113 Python tests. It generated a new immutable bundle at
`$POSE_EMBED_ARTIFACT_ROOT/manifests/ntu-input-v2-7721684` and compared each
of its eight JSONL files byte-for-byte with the historical release. No prior
bundle was overwritten. The novel-test opening ledger was absent.

- New `manifest-set.json` SHA-256:
  `a6023f13898310b500ff4af30d7545290eda554e8b8d3d4ef5456067b436aea9`.
- New generated `manifest-audit.md` SHA-256:
  `d7ad958e6e4f5a60c09ef6636bfbef0caab6296f93387ab1ada7985f37f18804`.
- Preserved Grid Engine log SHA-256:
  `8eb26fd4e226aa8c7d8da3c532758a56de6dda94b4450bf79b9f7e3a2b773f1b`.

The new generated audit reports `amendment_required: false`. This closes the
input/manifest contract gate only; it does not create the later evaluation
plan, final-run-set, protocol-lock, or test-opening artifacts.
