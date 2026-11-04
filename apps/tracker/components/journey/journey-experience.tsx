"use client";

import {
  ArrowDownOutlined,
  ArrowRightOutlined,
  CheckOutlined,
  ControlOutlined,
  LockOutlined,
  PauseOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { Button, ConfigProvider, theme } from "antd";
import { motion, useScroll } from "motion/react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { memo, useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { DataNotice } from "@/components/data-notice";
import { formatDateRange, weekProgress } from "@/lib/domain";
import { journeyWeeks, type JourneyStage } from "@/lib/journey-content";
import type { LoadedPlan, Week } from "@/lib/schema";

const JourneyScene = dynamic(() => import("./journey-scene"), { ssr: false });

type Recipe = "contrastive" | "contextual" | "supcon";
type Corruption = "clean" | "jitter" | "joints" | "frames";

function subscribeReducedMotion(listener: () => void) {
  const media = window.matchMedia("(prefers-reduced-motion: reduce)");
  media.addEventListener("change", listener);
  return () => media.removeEventListener("change", listener);
}

const getReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const getServerReducedMotion = () => false;

const sceneCopy: Record<JourneyStage, { title: string; caption: string; detail: string }> = {
  motion: {
    title: "Motion becomes a signature.",
    caption: "One clean reference. One query to recognize.",
    detail: "Original synthetic skeletons · no dataset samples",
  },
  encoder: {
    title: "Freeze the encoder. Learn the lens.",
    caption: "Pose sequence → 8,704 features → 2,048 values",
    detail: "Schematic representation · dimensions are not to scale",
  },
  space: {
    title: "A shared space. Three recipes.",
    caption: "Nearby points represent similar motion signatures.",
    detail: "Conceptual geometry · not measured embeddings",
  },
  corruption: {
    title: "Damage the query. Keep the reference.",
    caption: "The same realized damage is paired across every method.",
    detail: "Synthetic illustration · not an inference or accuracy result",
  },
  heads: {
    title: "Nine heads. One sealed test.",
    caption: "Three recipes × three seeds, all locked before opening.",
    detail: "Planned experiment structure · not checkpoint status",
  },
  results: {
    title: "A fair test earns an honest answer.",
    caption: "Measure every condition. Report every outcome.",
    detail: "Conceptual result matrix · no measured scores shown",
  },
};

const recipes: Array<{ key: Recipe; label: string; explanation: string }> = [
  { key: "contrastive", label: "Contrastive", explanation: "Pull same-action pairs together; push different-action pairs beyond a margin." },
  { key: "contextual", label: "Contextual", explanation: "Also compare local neighborhoods, using the full contextual recipe’s own margins and regularizer." },
  { key: "supcon", label: "SupCon", explanation: "Compare each example with its labeled positives and the rest of the batch. This arm is descriptive." },
];

const corruptions: Array<{ key: Corruption; label: string }> = [
  { key: "clean", label: "Clean" },
  { key: "jitter", label: "Jitter" },
  { key: "joints", label: "Missing joints" },
  { key: "frames", label: "Missing frames" },
];

function corruptionLabel(corruption: Corruption, severity: number) {
  if (corruption === "clean" || severity === 0) return "Clean query";
  if (corruption === "jitter") return `${[0, 1, 2.5, 5][severity]}% of torso scale`;
  if (corruption === "joints") return `${[0, 3, 6, 8][severity]} joint trajectories masked`;
  return `${[0, 10, 25, 40][severity]} of 100 frames masked`;
}

function StaticScene({ stage }: { stage: JourneyStage }) {
  return (
    <div className="journey-static" aria-hidden="true">
      <svg viewBox="0 0 600 540" fill="none">
        <ellipse cx="300" cy="285" rx="218" ry="208" stroke="currentColor" opacity=".18" />
        <ellipse cx="300" cy="285" rx="218" ry="70" stroke="currentColor" opacity=".18" transform="rotate(-24 300 285)" />
        <ellipse cx="300" cy="285" rx="90" ry="208" stroke="currentColor" opacity=".18" transform="rotate(24 300 285)" />
        {stage === "heads" || stage === "results" ? (
          Array.from({ length: 9 }, (_, i) => (
            <g key={i} transform={`translate(${195 + i % 3 * 78} ${168 + Math.floor(i / 3) * 83})`}>
              <path d="M0 13 27 0 54 13 27 27ZM0 13V48L27 62 54 48V13M27 27V62" stroke="currentColor" strokeWidth="1.5" />
              <circle cx="27" cy="31" r="4" fill="currentColor" />
            </g>
          ))
        ) : (
          <g stroke="currentColor" strokeWidth="2">
            <path d="M300 166V258L260 316 246 400M300 258 340 313 368 394M300 184 252 209 210 187M300 184 342 203 382 166" />
            {[ [300, 139], [300, 184], [300, 258], [260, 316], [246, 400], [340, 313], [368, 394], [252, 209], [210, 187], [342, 203], [382, 166] ].map(([x, y], i) => <circle key={i} cx={x} cy={y} r={i === 0 ? 24 : 5} fill={i === 0 ? "none" : "currentColor"} />)}
          </g>
        )}
        <path d="M110 456H490M300 448V464M160 452V460M440 452V460" stroke="currentColor" opacity=".3" />
      </svg>
    </div>
  );
}

const WeekChapters = memo(function WeekChapters({ weeks }: { weeks: Week[] }) {
  return journeyWeeks.map((chapter) => {
    const week = weeks.find((item) => item.number === chapter.number);
    if (!week) return null;
    const progress = weekProgress(week);
    return (
      <section
        className="journey-week journey-chapter"
        data-stage={chapter.stage}
        id={`week-${week.number}`}
        key={week.number}
        aria-labelledby={`week-title-${week.number}`}
      >
        <div className="journey-week-heading">
          <span className="journey-week-number" aria-hidden="true">{String(week.number).padStart(2, "0")}</span>
          <div>
            <p>Week {week.number} <span> / {formatDateRange(week.startDate, week.endDate)}</span></p>
            <span className={`journey-week-state state-${week.state}`}>
              {week.state === "closed" ? <CheckOutlined /> : week.state === "blocked" ? <LockOutlined /> : <span className="journey-state-dot" />}
              {week.state.charAt(0).toUpperCase() + week.state.slice(1)}
            </span>
          </div>
        </div>
        <h2 id={`week-title-${week.number}`}>{chapter.title}</h2>
        <p className="journey-question">{chapter.question}</p>
        <p className="journey-body">{chapter.action}</p>
        <div className="journey-evidence">
          <span>What this step produces</span>
          <p>{chapter.outcome}</p>
        </div>
        <p className="journey-why"><strong>Why it matters.</strong> {chapter.why}</p>
        <details className="journey-gates">
          <summary>Evidence & advancement gates <span>{progress.completed}/{progress.required} required tasks done</span></summary>
          <ul>
            {week.gates.map((gate) => <li key={gate.id}><span className="journey-gate-state">{gate.state}</span>{gate.criterion}</li>)}
          </ul>
          {week.gates.length === 0 ? <p>No explicit gates recorded for this week.</p> : null}
          <p>These are recorded tracker states. The calendar alone never marks work complete.</p>
        </details>
        <Link className="journey-text-link" href={`/weeks/${week.number}`}>Open Week {week.number} plan <ArrowRightOutlined /></Link>
      </section>
    );
  });
});

export function JourneyExperience({ weeks, dataSource, lastRefreshedAt }: Pick<LoadedPlan, "weeks" | "dataSource" | "lastRefreshedAt">) {
  const root = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState("the-question");
  const [scrollStage, setScrollStage] = useState<JourneyStage>("motion");
  const [sceneOverride, setSceneOverride] = useState<JourneyStage | null>(null);
  const [recipe, setRecipe] = useState<Recipe>("contextual");
  const [corruption, setCorruption] = useState<Corruption>("clean");
  const [severity, setSeverity] = useState(2);
  const [playing, setPlaying] = useState(true);
  const [view, setView] = useState(0);
  const [frame, setFrame] = useState(0);
  const [controlsOpen, setControlsOpen] = useState(false);
  const [sceneStatus, setSceneStatus] = useState<"loading" | "ready" | "unavailable">("loading");
  const reducedMotion = useSyncExternalStore(subscribeReducedMotion, getReducedMotion, getServerReducedMotion);
  const { scrollYProgress } = useScroll({ target: root, offset: ["start start", "end end"] });
  const stage = sceneOverride ?? scrollStage;
  const activeWeek = active.startsWith("week-") ? Number(active.slice(5)) : 0;
  const sceneReady = useCallback(() => setSceneStatus("ready"), []);
  const sceneUnavailable = useCallback(() => setSceneStatus("unavailable"), []);

  useEffect(() => {
    const chapters = Array.from(root.current?.querySelectorAll<HTMLElement>(".journey-chapter") ?? []);
    let frame = 0;
    let previous = "the-question";
    const update = () => {
      frame = 0;
      const marker = window.innerWidth <= 760 ? Math.min(window.innerHeight - 50, 430) : window.innerHeight * .5;
      let current = chapters[0];
      for (const chapter of chapters) {
        if (chapter.getBoundingClientRect().top <= marker) current = chapter;
      }
      if (current && current.id !== previous) {
        previous = current.id;
        setActive(current.id);
        setScrollStage(current.dataset.stage as JourneyStage);
        setSceneOverride(null);
      }
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(update); };
    update();
    // Request-streamed content can arrive after the browser's first hash jump.
    const anchor = document.getElementById(window.location.hash.slice(1));
    const anchorFrame = anchor && root.current?.contains(anchor)
      ? requestAnimationFrame(() => {
          anchor.scrollIntoView({ behavior: "instant", block: "start" });
          update();
        })
      : 0;
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      cancelAnimationFrame(frame);
      cancelAnimationFrame(anchorFrame);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, []);

  return (
    <div className="journey" ref={root} data-reduced-motion={Boolean(reducedMotion)}>
      <div className="journey-nav">
        <a href="#the-question" className="journey-nav-title">The research journey</a>
        <nav aria-label="Journey chapters">
          <a href="#the-question" aria-current={activeWeek === 0 && active !== "the-answer" ? "location" : undefined}>The idea</a>
          <a href="#week-1" aria-current={activeWeek > 0 ? "location" : undefined}>14 weeks</a>
          <a href="#the-answer" aria-current={active === "the-answer" ? "location" : undefined}>The answer</a>
        </nav>
        <motion.div className="journey-scroll-progress" style={{ scaleX: scrollYProgress }} />
      </div>

      <div className="journey-exhibition">
        <aside className="journey-stage" aria-label="Interactive experiment illustration" data-controls-open={controlsOpen}>
          <div className="journey-stage-top">
            <span>Pose Embed / an experiment in motion</span>
            <span className="journey-live-label"><span />Interactive 3D</span>
          </div>
          <div className="journey-scene-viewport" data-scene-state={sceneStatus}>
            <StaticScene stage={stage} />
            {sceneStatus !== "unavailable" ? <JourneyScene
              stage={stage}
              progress={activeWeek / 14}
              recipe={recipe}
              corruption={corruption}
              severity={severity}
              playing={playing && !reducedMotion}
              reducedMotion={Boolean(reducedMotion)}
              view={view}
              frame={frame}
              onReady={sceneReady}
              onUnavailable={sceneUnavailable}
            /> : null}
            {stage === "corruption" ? <div className="journey-query-labels"><span>Clean reference</span><span>Query · {corruption === "clean" || severity === 0 ? "clean" : "damaged"}</span></div> : null}
            <div className="journey-scene-caption">
              <p>{sceneCopy[stage].title}</p>
              <span>{sceneCopy[stage].caption}</span>
            </div>
          </div>
          <ConfigProvider theme={{ algorithm: theme.darkAlgorithm, token: { colorPrimary: "#ffffff", colorText: "#eeeeee", colorBgContainer: "#151515", borderRadius: 8, controlHeight: 36 } }}>
            <Button className="journey-mobile-controls-toggle" icon={<ControlOutlined />} aria-label={controlsOpen ? "Close controls" : "Explore controls"} aria-expanded={controlsOpen} aria-controls="journey-controls" onClick={() => setControlsOpen(!controlsOpen)}>{controlsOpen ? "Close controls" : "Explore controls"}</Button>
            <div className="journey-controls" id="journey-controls">
              <div className="journey-control-row">
                <span className="journey-control-label">Training recipe</span>
                <div className="journey-control-buttons" role="group" aria-label="Training recipe">
                  {recipes.map((item) => <Button key={item.key} aria-pressed={recipe === item.key} onClick={() => { setRecipe(item.key); setSceneOverride("space"); }}>{item.label}</Button>)}
                </div>
              </div>
              <p className="journey-control-explanation">{recipes.find((item) => item.key === recipe)?.explanation}</p>
              <div className="journey-control-row">
                <span className="journey-control-label">Query condition</span>
                <div className="journey-control-buttons" role="group" aria-label="Query condition">
                  {corruptions.map((item) => <Button key={item.key} aria-pressed={corruption === item.key} onClick={() => { setCorruption(item.key); setSceneOverride("corruption"); }}>{item.label}</Button>)}
                </div>
              </div>
              <div className="journey-severity">
                <label htmlFor="journey-severity">Corruption severity</label>
                <input id="journey-severity" type="range" min="0" max="3" step="1" value={corruption === "clean" ? 0 : severity} disabled={corruption === "clean"} onChange={(event) => { setSeverity(Number(event.target.value)); setSceneOverride("corruption"); }} aria-valuetext={corruptionLabel(corruption, severity)} />
                <output htmlFor="journey-severity">{corruptionLabel(corruption, severity)}</output>
              </div>
              <div className="journey-frame-control">
                <label htmlFor="journey-frame">Motion frame</label>
                <input id="journey-frame" type="range" min="0" max="99" value={frame} onChange={(event) => { setFrame(Number(event.target.value)); setPlaying(false); setSceneOverride("corruption"); }} aria-valuetext={`Frame ${frame + 1} of 100`} />
                <output htmlFor="journey-frame">{String(frame + 1).padStart(2, "0")} / 100</output>
              </div>
              <div className="journey-playback">
                <span>{sceneStatus === "unavailable" ? "3D unavailable · static illustration" : reducedMotion ? "Reduced motion · static chapter views" : "Explore the model"}</span>
                <Button icon={playing && !reducedMotion ? <PauseOutlined /> : <PlayCircleOutlined />} disabled={Boolean(reducedMotion) || sceneStatus === "unavailable"} onClick={() => setPlaying(!playing)} aria-label={playing && !reducedMotion ? "Pause animation" : "Play animation"} />
                <Button icon={<ReloadOutlined />} disabled={sceneStatus === "unavailable"} onClick={() => setView((value) => (value + 1) % 3)} aria-label="Rotate view" />
              </div>
              {sceneOverride ? <Button className="journey-resume" onClick={() => setSceneOverride(null)}>Resume chapter view</Button> : null}
            </div>
          </ConfigProvider>
          <p className="journey-illustration-note">{sceneCopy[stage].detail}</p>
        </aside>

        <div className="journey-story">
          <section id="the-question" className="journey-hero journey-chapter" data-stage="motion">
            <h1>One example.<br />{" "}<span>A world<br />{" "}of motion.</span></h1>
            <p>How do you recognize an action you have never learned—when the only clue is a damaged skeleton?</p>
            <a href="#the-representation" className="journey-start">Follow the experiment <ArrowDownOutlined /></a>
            <div className="journey-hero-foot"><span>14 weeks · September—December 2026</span><span>Scroll to discover</span></div>
          </section>

          <section id="the-representation" className="journey-chapter journey-concept" data-stage="encoder">
            <h2>Teach a new way<br />to see similarity.</h2>
            <p className="journey-lead">The action is unfamiliar.<br />The representation doesn’t have to be.</p>
            <p className="journey-body">MotionBERT turns a sequence of body joints into a motion signature. We freeze that encoder and train only a linear head: a new lens for comparing the signatures.</p>
            <ol className="journey-pipeline">
              <li><span>Input</span><strong>100 frames</strong><p>Two people · 17 joints · x, y, confidence</p></li>
              <li><span>Frozen MotionBERT</span><strong>8,704 features</strong><p>The same representation for every recipe</p></li>
              <li><span>Trainable linear head</span><strong>2,048 values</strong><p>Normalize, compare by cosine, retrieve</p></li>
            </ol>
            <p className="journey-why">At test time, one clean exemplar represents each of 20 unseen actions. A query retrieves the most similar exemplar. That is the one-shot task.</p>
          </section>

          <section id="the-recipes" className="journey-chapter journey-concept" data-stage="space">
            <h2>Same starting point.<br />Different geometry.</h2>
            <p className="journey-lead">Does the neighborhood around a motion help us recognize it under damage?</p>
            <p className="journey-body">Standard contrastive training works with pairs. The full contextual recipe also compares their neighborhoods. We test whether the complete recipe loses less accuracy when queries are corrupted.</p>
            <div className="journey-pairing">
              <div><strong>3 recipes</strong><span>Contrastive · Contextual · SupCon</span></div>
              <div><strong>3 paired seeds</strong><span>7 · 17 · 29</span></div>
              <div><strong>20 epochs</strong><span>Same duration, every run</span></div>
              <div><strong>8 × 4</strong><span>Actions × examples in a physical batch</span></div>
            </div>
            <p className="journey-why"><strong>The comparison has a boundary.</strong> Margins and regularization differ too, so an advantage would support the full recipe—not isolate the neighborhood term. SupCon is a descriptive comparator.</p>
          </section>

          <section id="the-stress-test" className="journey-chapter journey-concept" data-stage="corruption">
            <h2>Make the clue<br />harder to read.</h2>
            <p className="journey-lead">Keep the gallery clean.<br />Change only the query.</p>
            <p className="journey-body">Three separate stress tests, each at three nested severities. Every recipe sees the same damage. Try the query controls in the illustration.</p>
            <div className="journey-corruption-list">
              <div><strong>Coordinate jitter</strong><span>1% / 2.5% / 5% of torso scale</span><p>Perturb visible joint locations.</p></div>
              <div><strong>Missing joints</strong><span>3 / 6 / 8 trajectories</span><p>Mask the same selected joints across the sequence.</p></div>
              <div><strong>Missing frames</strong><span>10 / 25 / 40 of 100 frames</span><p>Mask a consecutive block without deleting time.</p></div>
            </div>
            <p className="journey-why">These are controlled tensor stress tests. They do not establish robustness to real camera occlusion or a different pose estimator.</p>
          </section>

          <div className="journey-calendar-intro">
            <h2>A question becomes<br />a sequence of proofs.</h2>
            <p>Fourteen weeks. Each step produces the evidence the next one needs. Explore any week, or keep scrolling.</p>
            <DataNotice dataSource={dataSource} lastRefreshedAt={lastRefreshedAt} />
          </div>
          <nav className="journey-week-nav" aria-label="Jump to research week">
            {journeyWeeks.map((week) => <a key={week.number} href={`#week-${week.number}`} aria-label={`Jump to Week ${week.number}`} aria-current={activeWeek === week.number ? "location" : undefined}>{String(week.number).padStart(2, "0")}</a>)}
          </nav>
          <WeekChapters weeks={weeks} />
        </div>
      </div>

      <section id="the-answer" className="journey-answer journey-chapter" data-stage="results">
        <div className="journey-answer-heading">
          <h2>The goal isn’t a win.<br /><span>It’s an answer<br />we can trust.</span></h2>
          <p>We expect contextual neighborhoods may help preserve retrieval under damage. The experiment is designed to find out—not to make that expectation come true.</p>
        </div>
        <div className="journey-outcomes">
          <div><span>01 / Contextual helps</span><h3>Less degradation.</h3><p>The prespecified conditional interval lies below zero. We can support a smaller accuracy drop for the full contextual recipe.</p></div>
          <div><span>02 / No clear advantage</span><h3>A useful null.</h3><p>The evidence does not resolve an advantage. We report the uncertainty, absolute accuracy, and every declared condition.</p></div>
          <div><span>03 / Contextual hurts</span><h3>A useful correction.</h3><p>The result runs against the hypothesis. We document where it fails and what the comparison can—and cannot—explain.</p></div>
        </div>
        <div className="journey-measure">
          <span>The prespecified comparison</span>
          <p>Δ = contextual accuracy drop − contrastive accuracy drop</p>
          <span>Negative means less degradation. A smaller drop alone does not mean better corrupted accuracy.</span>
        </div>
        <div className="journey-finish">
          <p>Three recipes. Twenty-seven selection runs. Nine final heads.<br />180 result cells. One defensible conclusion.</p>
          <Link href="/protocol/plan" className="journey-finish-link">Read the full research plan <ArrowRightOutlined /></Link>
          <Link href="/" className="journey-text-link">See recorded progress <ArrowRightOutlined /></Link>
        </div>
      </section>
    </div>
  );
}
