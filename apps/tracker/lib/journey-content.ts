export type JourneyStage =
  | "motion"
  | "encoder"
  | "space"
  | "corruption"
  | "heads"
  | "results";

export type JourneyWeek = {
  number: number;
  title: string;
  question: string;
  action: string;
  outcome: string;
  why: string;
  phase: "prepare" | "pilot" | "select" | "train" | "evaluate" | "explain";
  stage: JourneyStage;
};

// Public narrative of the canonical v3 calendar. Outcomes describe the intended
// evidence for each week, not completed experiments or changes to tracker state.
export const journeyWeeks: JourneyWeek[] = [
  {
    number: 1,
    title: "Define a fair question",
    question: "What would count as a trustworthy answer?",
    action:
      "Specify the retrieval question, verify licensed poses and the pretrained checkpoint, and measure the frozen encoder on an allocated GPU.",
    outcome:
      "A hash-bound starting protocol, an input inventory, and measured compute evidence.",
    why:
      "Agreeing on the rules before seeing test outcomes keeps a disappointing answer just as valid as an encouraging one.",
    phase: "prepare",
    stage: "motion",
  },
  {
    number: 2,
    title: "Separate learning from discovery",
    question: "Can we recognize an action we never trained on?",
    action:
      "Assign fixed identities to every sample. Separate 80 training actions, 20 development actions, and 20 unseen test actions; keep one clean test exemplar per action.",
    outcome:
      "Seven reproducible manifests and a leakage audit, including exact lists of excluded camera views.",
    why:
      "The primary queries exclude every synchronized view of the gallery performance, so another camera cannot give away the answer.",
    phase: "prepare",
    stage: "space",
  },
  {
    number: 3,
    title: "Build the sealed pipeline",
    question: "Can every result be traced back to its exact inputs?",
    action:
      "Version the frozen MotionBERT path for v3, verify retrieval and cache provenance, audit historical test access, and freeze the design before fresh extraction.",
    outcome:
      "A verified auxiliary-only preparation path with a fixed design, measured torso fallback, and registered artifact roots.",
    why:
      "Features, code, and protocol must agree. A new version name cannot erase prior test access or turn historical evidence into v3 results.",
    phase: "prepare",
    stage: "encoder",
  },
  {
    number: 4,
    title: "Prove the recipes can run",
    question: "Are we training the mathematics we intended?",
    action:
      "Verify loss values and gradients, paired initialization, and physical batches of eight actions × four examples. Generate fresh features and run one complete 20-epoch pilot per recipe.",
    outcome:
      "Three pilot records with checkpoints at epochs 5, 10, 15, and 20, plus numerical health, timing, memory, and storage evidence.",
    why:
      "Pilots test implementation and capacity. Their scores cannot pick learning rates, change the recipes, or select a shorter training duration.",
    phase: "pilot",
    stage: "encoder",
  },
  {
    number: 5,
    title: "Stress-test the experiment",
    question: "Can the entire study finish without changing its rules?",
    action:
      "Complete and rehearse the remaining execution and reporting path in one release. Revalidate its caches and pilots, audit the fixed geometry panel and all nine development corruptions, then check measured runtime, available time, and storage.",
    outcome:
      "Fresh release-bound evidence and an October 18 go/no-go decision with at least 25% work slack and a protected 200 GiB storage reserve.",
    why:
      "The full campaign must fit before selection begins. A failed gate calls for a documented result-blind amendment, not a smaller budget for one recipe.",
    phase: "pilot",
    stage: "corruption",
  },
  {
    number: 6,
    title: "Give every recipe the same chance",
    question: "Which learning rate works on clean, held-out actions?",
    action:
      "Begin 27 fresh development runs: three recipes × three learning rates × seeds 7, 17, and 29. Pair the initial heads and exact physical batches within each seed.",
    outcome:
      "Immutable attempts and clean development scores measured at the fixed epoch-20 endpoint.",
    why:
      "Equal attempted budgets make the comparison interpretable. Corrupted development scores and pilot weights stay outside selection.",
    phase: "select",
    stage: "space",
  },
  {
    number: 7,
    title: "Choose once, then commit",
    question: "Can another reader reproduce our selection?",
    action:
      "Finish all 27 attempts. Rank each recipe’s valid three-seed candidates by mean clean top-1, then mean reciprocal rank, then the lower learning rate.",
    outcome:
      "Three timestamped learning-rate choices and paired plans for final training on all 100 auxiliary actions.",
    why:
      "A candidate needs all three valid seeds. Keeping failures visible prevents a lucky partial result from becoming the selected configuration.",
    phase: "select",
    stage: "space",
  },
  {
    number: 8,
    title: "Train the final representations",
    question: "What geometry does each recipe learn?",
    action:
      "Start nine fresh linear heads on all 95,001 auxiliary examples. Keep MotionBERT frozen; train each recipe with the three paired seeds for exactly 20 epochs.",
    outcome:
      "Final training attempts with recorded initialization, batch plans, health diagnostics, and resource costs.",
    why:
      "Each head maps the same 8,704 features to 2,048 normalized values. Shared inputs let us compare the full training recipes under paired conditions.",
    phase: "train",
    stage: "heads",
  },
  {
    number: 9,
    title: "Account for every final head",
    question: "Are all nine models ready for the same test?",
    action:
      "Complete the nine final runs and audit their checkpoint hashes, exact update counts, and provenance. Declare both query definitions and every evaluation condition.",
    outcome:
      "Nine verified epoch-20 heads and a fixed matrix of 180 expected result cells.",
    why:
      "Pilot or development weights cannot substitute for final training. Every recipe and seed must be ready before unseen test evaluation begins.",
    phase: "train",
    stage: "heads",
  },
  {
    number: 10,
    title: "Rehearse the answer without opening it",
    question: "Will evaluation measure exactly what we promised?",
    action:
      "Independently repeat the evaluation and report checks rehearsed before selection. Verify rankings, ties, query subsets, all-head projection, and complete result accounting against the final implementation using fixtures and development data.",
    outcome:
      "A reviewed evaluator, verified opening controls, and report templates explicitly marked as non-final.",
    why:
      "We can fix a scoring defect before opening. After test outcomes are visible, changing the confirmatory pipeline would change the scientific claim.",
    phase: "evaluate",
    stage: "heads",
  },
  {
    number: 11,
    title: "Close the last escape hatches",
    question: "Is everything fixed before the unseen actions appear?",
    action:
      "Resolve audit findings and bind all nine checkpoints, exact sample lists, code, and evaluation rules into the final lock. Repeat seal and capacity checks by November 29.",
    outcome:
      "A complete authorization package, with Thanksgiving time reserved for recovery and any remaining blockers made explicit.",
    why:
      "Training must be finished, historical access resolved, and resources available. An unresolved prerequisite keeps the test sealed.",
    phase: "evaluate",
    stage: "heads",
  },
  {
    number: 12,
    title: "Open once. Measure everything.",
    question: "How much recognition survives damaged pose queries?",
    action:
      "Record the authorized opening before loading novel poses. Keep the gallery clean; evaluate clean queries and nine corruption conditions through every final head and both query definitions.",
    outcome:
      "180 provenance-verified cells with top-1, reciprocal rank, top-5 retrieval, and reproducible per-query ranks.",
    why:
      "All heads reuse the same encoded inputs and realized damage. A crash permits only the identical authorized retry; it never reseals the test.",
    phase: "evaluate",
    stage: "corruption",
  },
  {
    number: 13,
    title: "Let the evidence set the claim",
    question: "Does the full contextual recipe lose less accuracy?",
    action:
      "Compare clean-to-corrupted top-1 drops across the three paired seeds and nine conditions. Compute the prespecified conditional interval, then show absolute scores and every seed and cell.",
    outcome:
      "Reproducible curves, action sensitivity checks, resource tables, and a report and poster draft.",
    why:
      "Smaller degradation alone can hide poor accuracy. A contextual advantage requires the interval’s upper bound below zero; null and contrary outcomes remain successful findings.",
    phase: "explain",
    stage: "results",
  },
  {
    number: 14,
    title: "Make the answer recoverable",
    question: "Can someone follow the evidence all the way back?",
    action:
      "Run an independent reproduction smoke test, finish the report and poster, and archive permitted code, configurations, manifests, and compact summaries by December 18.",
    outcome:
      "A reproducible final study with explicit limits—or an honest incomplete-study record if the required campaign could not pass its gates.",
    why:
      "The deliverable is a defensible answer, not a promised win. Licensed poses, checkpoints, full run artifacts, and private records stay outside the public archive.",
    phase: "explain",
    stage: "results",
  },
];
