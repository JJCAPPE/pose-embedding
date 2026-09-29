import { readFileSync, writeFileSync } from "node:fs";

const repositoryRoot = new URL("../../../", import.meta.url);
const sources = {
  plan: {
    title: "Final v3 plan",
    sourcePath: "plan/research-plan.v3.md",
    filename: "research-plan.v3.md",
  },
  decision: {
    title: "V3 scope decision",
    sourcePath: "docs/decisions/0004-frozen-one-shot-v3.md",
    filename: "0004-frozen-one-shot-v3.md",
  },
};
const documents = Object.fromEntries(
  Object.entries(sources).map(([name, source]) => [name, {
    ...source,
    markdown: readFileSync(new URL(source.sourcePath, repositoryRoot), "utf8"),
  }]),
);
writeFileSync(new URL("../lib/protocol-documents.json", import.meta.url), `${JSON.stringify(documents, null, 2)}\n`);
