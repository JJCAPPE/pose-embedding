# Independent research governance

Effective 2026-09-24, at the researcher's explicit direction, this is an
independent research project. No advisor approval, sign-off, review meeting,
or delivery to an advisor is required to advance the plan. The researcher
records protocol decisions, result-blind amendments, review findings, and
evidence. Optional feedback does not create an external approval gate.

This governance record supersedes advisor requirements in the original
prospectus, historical decision notes, and
[protocol approval record](protocol-v1-approval.md). Those records and all
previous run artifacts remain preserved; they are not current prerequisites.

## Hash-bound change

- Previous protocol SHA-256:
  `12cf4d9a322f5bd5ea76fb2d9ffc070a6a2681fe8474a05cff1f62b6e43368e2`.
- Independent-research protocol SHA-256:
  `1b43d1bedb833f71936d0bc36d30a9b6f7ed6d2d00a5b8c8b781b787ad66d265`.
- The only protocol changes replace advisor-approved amendments with
  documented amendments. Protocol locks now require `recorded_by` and
  `recorded_at`, not advisor approval fields. Recorder identity, timestamp
  ordering, timezone, future-date rejection, and every hash binding remain
  mandatory. Existing locks must not be silently converted or overwritten.

No method, split, seed, batch, corruption, metric, estimand, claim rule,
dataset count, or source-verification contract changes in this revision.
The separate [input-contract amendment](input-contract-amendment-draft.md)
is not adopted by this governance change. Future artifacts must bind the
current digest; historical evidence continues to identify its original digest.

## Safeguards retained

Protocol amendments must be documented before novel-test opening and must not
use novel-test outcomes. The final-test command still requires the complete
protocol, evaluation-plan, manifest, and final-run-set locks. This governance
change neither creates those later-stage locks nor opens the test seal.

Dataset licensing, upstream attribution, and applicable BU requirements are
unchanged. The pending institutional determination is not an advisor approval
and is not waived here. Actual research time must still be recorded by the
researcher. No task, gate, or week is newly marked complete by this change.

The tracker retains its legacy `advisorPrompt` / `advisor_prompt` storage names
for compatibility, but presents them only as researcher review prompts under
“Research checkpoint.” They carry no advisor requirement.
