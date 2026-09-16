# Manifest files

The canonical format is UTF-8 JSON Lines. Each non-empty line has:

```json
{
  "sample_id": "S001C001P001R001A001",
  "relative_path": "optional/authorized/S001C001P001R001A001.pkl",
  "split": "novel_anchor",
  "is_anchor": true,
  "sha256": "required-for-file-verification-lowercase-digest"
}
```

Allowed splits are `development_train`, `development_validation`, `final_train`,
`novel_anchor`, `novel_query_primary`, and `novel_query_official`.

The Week 2 generator writes seven physical split files. `official-novel.jsonl`
is the source-order union of `novel_anchor` and `novel_query_official` records;
it deliberately does not invent a seventh split value. Cross-file repetition is
expected, while every individual file must contain unique sample IDs.

Generate manifests only after the official one-shot anchor list has been
obtained. Run `pose-embed data verify --manifest <path>` before feature
extraction. The verifier checks NTU identifiers, action partitions, duplicate
records, class leakage, and anchor-performance leakage in the primary query set.
Filenames must begin with exactly the declared canonical sample ID and may only
add dot-separated extensions. Paths must be normalized relative POSIX paths;
traversal, multiple path aliases for one sample, and one path assigned to
multiple samples are rejected.

## Trusted aggregate inventory

The licensed input is one hash-pinned `ntu120_hrnet.pkl` container, not one file
per sample. Do not repeat the container path or digest 113,945 times and do not
fabricate per-row checksums. `source-inventory.jsonl` instead records normalized
metadata for each aggregate annotation:

- canonical sample ID plus setup, camera, performer, repetition, and action;
- zero-based aggregate label and source annotation index;
- pose-track and nonempty-track counts;
- total frames, keypoint/confidence shapes, and image/original shapes.

The filename encodes only `S/C/P/R/A`; pose-track metadata comes from the
hash-verified annotation arrays. The generated `manifest-set.json` binds the
aggregate and official missing-skeleton hashes, the protocol hash, every output
checksum, counts by class, and every primary-query exclusion.

When the final evaluation plan is populated, its source-inventory binding must
use `kind: ntu_aggregate_inventory` and copy the aggregate, missing-list, byte,
hash, missing-count, and nominal-count fields recorded by the bundle. The test
seal then rehashes both physical inputs, re-inspects the aggregate, and requires
its normalized records to equal the locked inventory exactly; evaluation subset
rows deliberately make no per-sample file or checksum claim. The currently
locked 114,480-row expectation still fails closed until the documented
result-blind amendment is approved. That amendment must bind both the 113,945
usable-row count and this aggregate-plus-missing-list verification contract in
place of the protocol's current per-sample-file requirement.

Generate one immutable bundle below the artifact root with:

```sh
pose-embed data generate \
  --data-root "$POSE_EMBED_DATA_ROOT" \
  --output-dir "$POSE_EMBED_ARTIFACT_ROOT/manifests/ntu120-v1"
```

The output directory must not already exist. The command verifies both source
files before unpickling, rejects malformed or duplicate identities, validates
labels and pose shapes, proves all split relations, and writes atomically.
