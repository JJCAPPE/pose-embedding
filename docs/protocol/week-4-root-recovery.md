# Week 4 historical-artifact recovery — October 8, 2026

**Status: historical-root retirement resolved by dated cleanup evidence and
researcher attestation; existing runtime gates still apply.**
This note supplements [Week 3 readiness](week-3-v3-readiness.md) and the
[v3 SCC runbook](scc-v3-runbook.md). V3 remains the active scientific plan. The
retired worktree names identify historical evidence locations, not a return to
v2. The missing artifact files have not been recovered or recreated.

## Original audit and current observations

The immutable local audit recorded on September 29, 2026, at
21:28:20.522052 UTC inspected three historical artifact roots. Its SHA-256 is
`7cc2595dffcc92379d18877d5520aa0c41bfb31b2840898c979adddd30d23cd1`, bound to source
inventory `e0ab842fe2a62b50ff7205d0f8658fad373a03c5b29527c281a2db0225ea0058`.
Root nicknames below avoid publishing private filesystem paths.

| Historical root | Files in September 29 audit | October 8 observation |
| --- | ---: | --- |
| `motion-retrieval-v2` worktree artifacts | 7 | Checkout and artifact directory absent |
| `week3-scc-ready` worktree artifacts | 85 | Checkout and artifact directory absent |
| Main checkout artifacts | 52 | 52 readable files; no opening record found |

The October 8 SCC inspection searched both registered SCC artifact roots and
the SCC release and repository directories for filenames containing `opening`.
The bounded search completed at 18:52:34 UTC with no matches or errors. It did
not follow symbolic links and does not establish readability of every linked
location. The immutable registry and lock hashes were also checked. These
observations alone do not resolve the missing local roots or the interval after
their September 29 audit. No scientific job had been submitted at that preflight.

## Dated removal evidence

Retained desktop application logs identify automatic worktree `startup-cleanup`
on October 5, 2026. They record successful Git snapshots followed by successful
forced worktree removal:

| Worktree | Removal completed (America/New_York) | Preserved snapshot commit |
| --- | --- | --- |
| `motion-retrieval-v2` | October 5, 15:39:05.540 EDT | `3e9629561d2ee1e1b9202410aa08daa2c8bffe13` |
| `week3-scc-ready` | October 5, 15:39:15.763 EDT | `833fd2c7fd000938656d1ce9663f00347ef42489` |

The corresponding `refs/codex/snapshots/` references remain available locally.
Both snapshot trees were inspected and contain no `artifacts/` files. The
ignored artifact directories were outside the Git snapshot; restoring source
code from these references would not recover that evidence. The retained
pre-v3 backup archive contains 41 source files and no artifact-directory files.
The original logs and exact private reference locations remain outside Git.

## Researcher resolution and remaining safeguards

The dated cleanup explains why the checkout directories disappeared. It does
not show what the ignored directories contained immediately before removal,
recover the missing files, or establish uninterrupted sealed status between
September 29 and October 5. The bounded search has not located recoverable
copies; it does not establish that no other backup exists. The 7 and 85 files
recorded in those roots, 92 files in total, remain missing. This note does not
claim that their exact contents have been reconstructed or that every file has
a verified remote duplicate.

On October 8, the researcher was explicitly asked whether they had run anything
or accessed novel data since the September 29 audit. They answered no and
authorized proceeding without recreating the retired directories unless
strictly necessary. This first-person factual attestation, together with the
original sealed audit and the dated automatic cleanup records, resolves the
intervening historical-root question for continued v3 preparation. Absence of
files alone is not the basis for this resolution.

Retain the original audit, registry, locks and all surviving evidence unchanged.
Record the retirement and researcher attestation in a supplemental immutable
SCC audit resolution, refresh the bounded checks of the surviving roots, and
pass the existing runtime guards before fresh v3 extraction or pilots. No blank
replacement directories were created, and the missing roots were not silently
removed from the registry. This factual retirement resolution changes no
scientific recipe, split, method, implementation or protocol hash and requires
no scientific amendment. It does not authorize selection, final training or
novel access.
