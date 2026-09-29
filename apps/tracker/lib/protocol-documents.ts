import documents from "@/lib/protocol-documents.json";

// These two public documents are bundled with the deployment. The consistency
// test requires byte-for-byte agreement with their tracked source documents.
export const protocolDocuments = documents;
export type ProtocolDocumentName = keyof typeof protocolDocuments;

export function isProtocolDocumentName(name: string): name is ProtocolDocumentName {
  return name === "plan" || name === "decision";
}

export function protocolDocumentLink(href: string): string {
  if (href.endsWith("/research-plan.v3.md")) return "/protocol/plan";
  if (href.endsWith("/0004-frozen-one-shot-v3.md")) return "/protocol/decision";
  if (href === "../docs/proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf") {
    return "https://github.com/JJCAPPE/pose-embedding/blob/47ca528a99048278693e28019f52d8e924d7e270/docs/proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf";
  }
  return href;
}

export function documentHeadingId(heading: string): string {
  return heading.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}
