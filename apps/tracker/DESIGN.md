---
name: Pose Embed
description: A quiet research briefing for protocol-led work and decisions.
colors:
  ink-strong: "#000000"
  action: "#111111"
  ink: "#1d1d1f"
  ink-hover: "#333333"
  muted: "#6e6e73"
  line: "#d2d2d7"
  line-soft: "#e5e5e7"
  selected: "#e8e8ed"
  surface-subtle: "#f5f5f7"
  surface-raised: "#fbfbfd"
  surface: "#ffffff"
typography:
  display:
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif'
    fontSize: "clamp(2.5rem, 5vw, 4.5rem)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-0.04em"
  headline:
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif'
    fontSize: "clamp(1.55rem, 2.8vw, 2.15rem)"
    fontWeight: 660
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  title:
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif'
    fontSize: "17px"
    fontWeight: 630
    lineHeight: 1.4
    letterSpacing: "-0.015em"
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif'
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif'
    fontSize: "12px"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "0.02em"
rounded:
  control-sm: "8px"
  compact: "10px"
  control: "12px"
  list: "14px"
  surface: "16px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "18px"
  lg: "24px"
  xl: "32px"
  section: "44px"
  major: "72px"
components:
  button-primary:
    backgroundColor: "{colors.action}"
    textColor: "{colors.surface}"
    typography: "{typography.body}"
    rounded: "{rounded.compact}"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.ink-hover}"
    textColor: "{colors.surface}"
  button-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.compact}"
    height: "44px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.compact}"
    padding: "10px 12px"
    height: "44px"
  navigation-item:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    typography: "{typography.body}"
    rounded: "{rounded.compact}"
    padding: "0 16px"
    height: "38px"
  navigation-item-selected:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.action}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.surface}"
    padding: "24px"
  deliverable-card:
    backgroundColor: "{colors.ink-strong}"
    textColor: "{colors.surface}"
    rounded: "{rounded.surface}"
    padding: "24px"
---

# Design System: Pose Embed

## Overview

**Creative North Star: "The Quiet Research Briefing"**

Pose Embed should feel like a calm, carefully prepared briefing placed in front of a researcher and advisor. The interface is restrained and direct: one clear question, action, deliverable, or decision leads each work surface, while supporting evidence waits at the next level of hierarchy.

The system is strictly black, white, and neutral gray. Apple-like system typography, generous whitespace, precise dividers, modest rounding, and progressive disclosure keep dense protocol content readable without making it feel ornamental or promotional. Ant Design supplies the interaction primitives; the visual system makes them feel native to this quiet research workspace.

**Key Characteristics:**

- Strict black, white, and neutral gray.
- Action-first hierarchy before technical detail.
- Generous whitespace with precise, low-contrast dividers.
- Ant Design primitives with calm, consistent states.
- Progressive disclosure for scientific and operational depth.

## Colors

The palette is entirely achromatic: solid black anchors commitments and primary actions, white carries content, and a narrow neutral ramp separates text, dividers, selections, and the page canvas.

### Primary

- **Commitment Black:** The strongest ink marks primary actions, decisive headings, completed states, and the inverted deliverable band.
- **Action Charcoal:** Ant Design's primary interaction color provides a slightly softened black for controls and progress.

### Neutral

- **Reading Ink:** Default copy uses a softer near-black for comfortable sustained reading.
- **Hover Charcoal:** Primary controls move to this lighter black on hover and keyboard focus.
- **Muted Graphite:** Secondary copy, labels, dates, and supporting metadata recede without losing legibility.
- **Structural Line:** Standard control and card borders define boundaries without visual weight.
- **Quiet Divider:** Internal separators and list rules organize dense records.
- **Selected Gray:** Active navigation, active work states, and segmented selections use a neutral fill rather than hue.
- **Workspace Gray:** The application canvas separates white content surfaces from the page.
- **Raised Paper:** Slightly warmer white-gray supports loading and raised-surface nuance.
- **Paper White:** Primary cards, inputs, drawers, and the header use clean white.

**The No Hue Rule.** Do not introduce semantic or decorative hues; encode meaning with labels, icons, weight, fill, border, and line style.

## Typography

**Display Font:** Apple system sans-serif (with Helvetica Neue and Arial fallbacks)
**Body Font:** Apple system sans-serif (with Helvetica Neue and Arial fallbacks)

**Character:** The single system stack is calm, familiar, and platform-native. Tight display tracking creates authority at the top of a page; body copy immediately returns to neutral proportions and generous leading.

### Hierarchy

- **Display** (700, fluid 2.5rem–4.5rem, 0.98 line-height): Plain-language page questions and top-level outcomes; keep lines short and balanced.
- **Headline** (660, fluid 1.55rem–2.15rem, 1.1 line-height): Major section headings that organize the briefing.
- **Title** (630, 17px, 1.4 line-height): Week, record, and list-item titles in dense operational views.
- **Body** (400, 15px, 1.5 line-height): Default reading and control text; long explanations stay near 72 characters per line.
- **Label** (650, 12px, 0.02em letter-spacing): Eyebrows, card labels, metrics, and compact metadata; use sentence case rather than loud all-caps.

**The Brief Before Detail Rule.** Use the strongest type for the plain-language question or required action, then step down quickly to calm body copy and compact labels.

## Layout

The desktop canvas centers a maximum-width 1240px shell with 24px side clearance, expanding to 40px in the header. Pages use 44px top and 88px bottom padding, with 72px separating major sections. Reading copy is constrained to roughly 72 characters.

Action-led pages open with a wide primary-action card and a narrower decision card, followed by a full-width deliverable band. Work pages must surface Next step, Decision needed, Deliverable, and a plain-language summary before technical detail. Week pages use a wider work column and a narrower supporting column; supporting detail may remain sticky while space permits.

At 900px, navigation moves into a drawer and split grids become single columns. At 680px, the shell uses 16px side clearance, page padding tightens, headings remain fluid, metrics stack, primary actions become full-width, and dense rows reorganize into readable vertical groups. Mobile ordering preserves the briefing sequence rather than shrinking the desktop composition.

## Elevation & Depth

The system is flat and border-led at rest. White surfaces sit on the workspace-gray canvas, precise lines separate adjacent information, and the black deliverable band gains prominence through contrast rather than lift. Shadows are limited to floating navigation, contained authentication surfaces, and a subtle one-pixel hover rise on interactive list cards.

### Shadow Vocabulary

- **Contained Surface** (`0 8px 30px rgba(0, 0, 0, 0.06)`): Low ambient separation for a focused panel such as authentication.
- **Floating Surface** (`0 16px 48px rgba(0, 0, 0, 0.08)`): Drawers and truly floating overlays only.
- **Interactive Lift** (`0 10px 28px rgba(0, 0, 0, 0.05)`): Quiet hover feedback on clickable week and record rows.

**The Flat-by-Default Rule.** Keep working surfaces flat and border-defined; reserve shadows for floating overlays, contained authentication surfaces, and subtle hover feedback.

## Shapes

Corners are gently rounded rather than pill-like. Controls use compact 8px–12px radii, list rows use 14px, and primary surfaces use 16px. The 32px square wordmark uses a tighter 9px corner; circular geometry is reserved for compact decision indices and familiar status icons. One-pixel neutral borders remain visible on white surfaces, while blocked or waiting states may use a dashed border to communicate status without color.

## Components

### Buttons

- **Shape:** Compact rounded rectangle with a 10px radius and 44px standard control height.
- **Primary:** Action charcoal with white text and 600 weight; one clear primary action should lead a work region.
- **Hover / Focus:** Hover shifts to hover charcoal over a 160–180ms transition. Keyboard focus uses a 3px black outline with a 3px offset.
- **Secondary:** White with reading ink and a structural-line border; use for return, cancel, and supporting actions.

### Status Tags

- **Style:** Compact neutral tags pair an icon with a plain-language label. Default states are white with a structural-line border.
- **State:** Done, met, and closed invert to black; active and ready use selected gray; blocked and waiting use dashed borders; skipped and waived use muted struck-through text.

### Cards / Containers

- **Corner Style:** Primary surfaces use 16px corners; compact list rows use 14px.
- **Background:** Paper white on the workspace-gray canvas. The deliverable card alone inverts to black and white.
- **Shadow Strategy:** Flat at rest; use the limited vocabulary in Elevation & Depth.
- **Border:** One-pixel structural or quiet-dividing gray.
- **Internal Padding:** 24px by default, tightening to 20px on narrow screens.

### Inputs / Fields

- **Style:** White, 44px tall, structural-line border, 10px radius, and 10px by 12px internal padding. Labels are 13px and semibold; help text is smaller and muted.
- **Focus:** Border moves to action charcoal with a restrained 3px translucent black ring.
- **Error / Disabled:** Keep the palette monochrome; pair any state change with explicit text and an icon, never color alone.

### Navigation

The desktop header is a slim translucent white bar with a subtle bottom rule. Navigation items are 38px high, use muted text at rest, and gain a quiet gray background with dark text when hovered or selected. At 900px, replace the horizontal navigation with a right-side drawer whose vertical menu preserves the same selected treatment.

### Priority Brief

This signature composition places Next step and Decision needed side by side, then spans Deliverable below them in an inverted black band. The next action receives the only primary button; decision items are separated by fine rules and numbered circles. On small screens the cards stack without losing the action → decision → deliverable reading logic within the component.

## Do's and Don'ts

### Do:

- Do surface Next step, Decision needed, Deliverable, and a plain-language summary before technical detail on work pages.
- Do keep meaning independent of color through explicit labels, icons, fill, border, and line style.
- Do preserve 44px standard controls, visible focus rings, and reduced-motion behavior.
- Do use whitespace and dividers to organize dense records before adding containers or decoration.

### Don't:

- Don't introduce hue, gradients, or decorative accent colors.
- Don't turn a research work page into a marketing hero or generic analytics dashboard.
- Don't use shadows as the default boundary for cards and sections.
- Don't make technical details compete with the primary briefing; place them in supporting sections or disclosure controls.
- Don't collapse status distinctions to fill alone.
