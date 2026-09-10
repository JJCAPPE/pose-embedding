---
version: 1
slug: "app-page-tsx"
primary_target: "app/page.tsx"
related_targets: ["app/layout.tsx","app/protocol/page.tsx","app/literature/page.tsx","app/weeks/[number]/page.tsx","app/edit/page.tsx","app/edit/weeks/[number]/page.tsx"]
---

# Overview surface brief

- Scope: `app/page.tsx` and the shared visual grammar carried across every tracker route.
- Mode: Operate.
- Audience: student research owner first; advisor and public reviewers second.
- Job: understand what the study is, what happens next, what must be delivered, and what decision blocks advancement.
- Primary action: open the first non-closed week and act on its first unfinished required task.
- Proof and content: tracked plan, task evidence, required gates, schedule, protocol, and verified sources only.
- Constraints: preserve public/private boundaries, native server-action forms, optimistic concurrency, cached public reads, semantic lists, and exact scientific content.
- Direction: monochrome Apple-inspired research review workspace built from Ant Design, with a decision-led split and progressive disclosure.
- Approved comp: `.impeccable/mocks/overview-decision-split.png`.
- Memorable moment: the first scan reads as an honest briefing—Do next, Deliver this week, Decide before advancing—before any progress metric or technical detail.
- Unresolved: manual actions lack an explicit completion field; the UI must not invent one.

## Composition and implementation inventory

| Visible ingredient | Commitment | Medium |
| --- | --- | --- |
| Global navigation | Slim translucent top bar; clear active route; mobile drawer | Ant Design Layout, Menu, Drawer; semantic Next links |
| Plain-language opening | Compact heading and project summary, never a marketing hero | Semantic HTML plus Ant Typography |
| Do next | Dominant left region with first unfinished required task and one primary action | Ant Card, Button, Tag, Progress |
| Decide before advancing | Narrower ledger of pending required gates; read-only on public pages | Ant List and Tag |
| Deliverable | Full-width commitment band directly below action/decision split | Ant Card and Typography |
| Study plan | Dense but quiet 14-week list with filters and state/readiness distinguished | Ant Segmented, List, Progress, Tag |
| Public data fallback | Compact, non-alarming saved-snapshot notice | Ant Alert |
| Supporting detail | Technical/scientific detail closed until requested | Ant Collapse, Tabs, Descriptions |
| States and feedback | Shape, icon, label, fill, and border carry meaning without hue | Ant Result, Empty, Skeleton, Alert, Tag |
| Responsive behavior | Summary stacks action → deliverable → decision; schedule becomes single-column; drawer replaces desktop nav | CSS Grid/media queries plus Ant Grid hooks where client-side behavior is needed |
