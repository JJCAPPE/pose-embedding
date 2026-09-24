# Input-contract amendment v1 — adopted

Status: **adopted before novel-test opening**. Recorded
2026-09-24T16:25:10Z under the [independent research governance](independent-research.md).
The researcher explicitly directed implementation without advisor approval on
2026-09-24. This is a result-blind input-accounting correction, not a change
made in response to retrieval outcomes. The novel-test opening ledger was
absent at the time of the decision; the SCC rerun must confirm that again.

Previous protocol canonical SHA-256:
`1b43d1bedb833f71936d0bc36d30a9b6f7ed6d2d00a5b8c8b781b787ad66d265`.
Adopted amended protocol canonical SHA-256:
`c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.
The latter is from `pose-embed protocol verify`; future scientific artifacts
must bind it. Historical locks and manifest bundles retain their original
hashes and remain historical records.

## Decision and evidence

The complete usable HRNet source inventory is exactly **113,945 unique pose
annotations**, not 114,480 per-sample pose files. The NTU authors' official
missing-skeleton list contains **535 unique excluded nominal captures**. The
sets do not overlap; together they account for **114,480 nominal captures**.
No placeholder pose rows are permitted. The usable aggregate includes all 120
actions and all 20 official one-shot exemplars. The original
[manifest audit](ntu-manifest-audit.v1.md) and
[source metadata](../../data/manifests/ntu120-hrnet.v1.json) establish this
result-blind input evidence. The original audit is preserved as a snapshot of
the pre-amendment gate state.

Paths below are relative to `POSE_EMBED_DATA_ROOT`. Licensed files remain
outside Git.

| Physical input | Bytes | SHA-256 |
| --- | ---: | --- |
| `ntu120_hrnet.pkl` | 1,238,461,428 | `aaf1f928b4629fa9a0850528d43fdd8d920532805d16672bfdda78085b649df8` |
| `provenance/sources/NTU_RGBD120_samples_with_missing_skeletons.txt` | 11,451 | `ab14fe64e89be63d2b08141713fcc31f6ebc7b01955009c3585d8d3367e0facc` |

The official list is pinned to NTURGB-D commit
`ac2ebc87e6e9777ea6bac67e65e53b325b903f74`. The eight immutable JSONL
files (one source inventory and seven split manifests) retain these verified
row counts and SHA-256 digests:

| JSONL file | Rows | SHA-256 |
| --- | ---: | --- |
| `source-inventory.jsonl` | 113,945 | `e0ab842fe2a62b50ff7205d0f8658fad373a03c5b29527c281a2db0225ea0058` |
| `development-train.jsonl` | 76,013 | `2278b58090dbd3a00255936c8e4a2bd40887af995a88672334e4ed296605661c` |
| `development-validation.jsonl` | 18,988 | `339f330d21e8a4bb712585d8c4074adac0adfad253c9046d3a397451f2f69b15` |
| `final-train.jsonl` | 95,001 | `5775b0b05dd2c80504433273d620069c64804a705a8f373a217e318c4aa28622` |
| `official-novel.jsonl` | 18,944 | `44a0da454a930530e56a6a398ede145cc6f8f0258403c01df7676305c143ba1c` |
| `novel-anchor.jsonl` | 20 | `176cd1715bfdff30613381834b90c7e0aba434648780e0ea435f2ccaab440d30` |
| `novel-query-primary.jsonl` | 18,884 | `c401ee11b3b0965ce46c3fb06e30eaa4859efbc8eb74931273ad793f77d9b4b9` |
| `novel-query-official.jsonl` | 18,924 | `cf74650e6c0d5fda31d4a3dc59fcd3825ca0b8f166e1963d85ac449d525412e9` |

At initial test opening, the evaluation plan must bind the exact two-file
source contract and all ordered manifest identities. The validator verifies
both physical files by size and SHA-256, re-inspects the trusted aggregate,
checks the 535-list and its non-overlap, and compares the complete derived
inventory and query subsets. The immutable opening ledger binds the protocol,
evaluation plan, source inventory, physical-file count **2**, and combined
source digest. Later cells rely on the already-verified immutable feature
caches rather than reopening the 1.2 GB pickle.

All methods, splits, seeds, preprocessing, corruptions, metrics, estimand,
claim rule, and result-blind selection remain unchanged. This decision does
**not** create an evaluation-plan or final-run-set lock, open the novel test,
waive dataset terms or BU data-governance determination, record research time,
or close Week 1. Those remain separate controls.
