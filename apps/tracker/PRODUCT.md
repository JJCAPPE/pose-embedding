# Product

<!-- impeccable:product-schema 1 -->

> The product facts below are inferred from the tracked plan, protocol, application behavior, tests, and the September 9, 2026 redesign brief. They should be confirmed with the project owner when convenient.

## Platform

web

## Users

The primary user is the student researcher who plans and closes weekly work, records evidence, and makes protocol-gated decisions. The advisor is the primary reviewer. Public visitors can inspect the public-safe schedule and progress without signing in.

## Product Purpose

Pose Embed turns a fourteen-week research protocol into an inspectable sequence of work, evidence, deliverables, and advancement decisions. Success means completing and communicating the locked study faithfully, including when the contextual method produces a null or negative result.

## Positioning

The tracker connects each weekly task to expected evidence and explicit gates while preserving a public advisor view and an authenticated, auditable owner workflow. It is a research decision record, not a generic project-management dashboard.

## Operating Context

The study runs from September 15 through December 18, 2026. The researcher works from the plan week by week, the advisor reviews progress and decisions, and public visitors can follow the public-safe record. The application always has a checked-in read-only plan; configured deployments can load live progress from Supabase. Owner edits publish to the advisor view.

## Capabilities and Constraints

- Public routes show the plan overview, weekly work, the locked protocol, the literature ledger, and public exports.
- The owner workspace edits weeks, tasks, expected evidence, gates, reflections, sources, and weekly source links.
- Closing a week requires its required work and gates to be resolved. Reopening a closed week requires an audited reason; reflections remain editable while closed.
- Mutations preserve version-checked optimistic concurrency and the existing Supabase authorization boundary.
- Public surfaces must not expose owner identity, activity history, secrets, licensed data locations, participant information, or private correspondence.
- The immutable seed remains a fallback, not a second editable store.

## Brand Commitments

The product name is Pose Embed. The requested replacement interface uses Ant Design throughout, a black-and-white monochrome palette, and Apple-inspired clarity, restraint, progressive disclosure, typography, spacing, and interaction behavior.

## Evidence on Hand

- `plan/research-plan.v1.json` contains the public-safe schedule, deliverables, gates, sources, and protocol summary.
- `docs/protocol/protocol-v1.md` and the tracked prospectus define the scientific scope and claim rules.
- Supabase provides live progress and owner-only activity history when configured.
- No testimonials, commercial claims, participant material, or novel-test outcomes should be fabricated for the interface.

## Product Principles

1. State the next meaningful step before presenting detail.
2. Make the expected deliverable concrete and easy to find.
3. Separate decisions and approval gates from ordinary tasks.
4. Start with plain-language context, then reveal scientific and operational detail progressively.
5. Preserve the locked protocol, honest reporting, and public/private boundary over visual convenience.

## Accessibility & Inclusion

The responsive web interface must remain keyboard navigable, preserve a skip link and semantic landmarks, expose visible focus states, respect reduced-motion preferences, and continue passing the existing automated accessibility checks.
