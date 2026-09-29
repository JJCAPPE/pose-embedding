# Preserve numeric JSON protocols before Week 4 extraction

Recorded September 29, 2026, under the researcher's instruction to complete
Week 3 and prepare for Week 4. This is a result-blind implementation correction;
the final v3 scientific design and its numeric settings are unchanged.

SCC job `7790703` completed auxiliary-only packaging, the prescribed fallback
measurement and exact-identity manifest rebinding. Its final freeze validation
then rejected `1e-08`, `1e-05` and `1e-06`: the configuration loader parsed the
canonical JSON file through YAML, whose numeric inference treated those JSON
numbers as strings. Independent verification job `7790712` reproduced the same
failure. Both failed job records and all preparation outputs are retained.
No v3 feature cache, pilot, or novel representation/outcome was produced.

The loader now parses `.json` configurations with the JSON parser. YAML input
behavior is unchanged, and quoted fixed numeric constants still fail v3
validation. A regression test reproduces the SCC failure through the actual
immutable JSON writer and checks round-trip model and protocol-digest equality
for both v1 and v3.

The failed freeze had already written its two canonical files. Preserve their
exact bytes and SHA-256 values beneath that failed attempt's launcher directory
before issuing a corrected design lock. Record the move, old/new release and
changed code hash in an immutable recovery record. This recovery is permitted
only before any v3 cache or pilot and while all registered dataset seals remain
unopened. No opening record is removed or changed.

The completed auxiliary preparation and rebound manifests can be reused because
their source hashes, identities, preprocessing, fallback measurement and resolved
protocol values are unchanged. The successful replacement freeze must validate
all those bindings and bind the corrected loader's code hash. Subsequent Week 4
work uses that new design lock. This does not authorize selection, final training
or novel access; those later-stage gates remain closed.
