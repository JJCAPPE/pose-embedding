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

Generate manifests only after the official one-shot anchor list has been
obtained. Run `pose-embed data verify --manifest <path>` before feature
extraction. The verifier checks NTU identifiers, action partitions, duplicate
records, class leakage, and anchor-performance leakage in the primary query set.
Filenames must begin with exactly the declared canonical sample ID and may only
add dot-separated extensions. Paths must be normalized relative POSIX paths;
traversal, multiple path aliases for one sample, and one path assigned to
multiple samples are rejected.
