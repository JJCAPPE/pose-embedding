import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  documentHeadingId,
  isProtocolDocumentName,
  protocolDocumentLink,
  protocolDocuments,
} from "@/lib/protocol-documents";

type DocumentPageProps = { params: Promise<{ document: string }> };

export function generateStaticParams() {
  return Object.keys(protocolDocuments).map((document) => ({ document }));
}

export async function generateMetadata({ params }: DocumentPageProps): Promise<Metadata> {
  const { document } = await params;
  if (!isProtocolDocumentName(document)) notFound();
  return { title: protocolDocuments[document].title };
}

export default async function ProtocolDocumentPage({ params }: DocumentPageProps) {
  const { document } = await params;
  if (!isProtocolDocumentName(document)) notFound();
  const source = protocolDocuments[document];
  const [title, ...body] = source.markdown.split("\n");
  const sections = [...source.markdown.matchAll(/^## (.+)$/gm)].map((match) => match[1]);

  return (
    <div className="shell page-shell protocol-document">
      <nav className="document-links" aria-label="Protocol documents">
        <Link href="/protocol">Protocol overview</Link>
        <Link href={document === "plan" ? "/protocol/decision" : "/protocol/plan"}>
          {document === "plan" ? "Scope decision" : "Final v3 plan"}
        </Link>
        <a href={`/protocol/${document}/source`} download={source.filename}>Download Markdown</a>
      </nav>
      <header className="page-header">
        <p className="eyebrow">Public planning record · September 29, 2026</p>
        <h1>{title.replace(/^# /, "")}</h1>
      </header>
      {sections.length > 0 ? (
        <nav className="document-contents" aria-label="On this page">
          <strong>On this page</strong>
          <ol>
            {sections.map((section) => (
              <li key={section}>
                <a href={`#${documentHeadingId(section)}`}>{section.replace(/^\d+\. /, "")}</a>
              </li>
            ))}
          </ol>
        </nav>
      ) : null}
      <article className="markdown-text">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ href, children }) => <a href={protocolDocumentLink(href ?? "")}>{children}</a>,
            h2: ({ children }) => <h2 id={documentHeadingId(String(children))}>{children}</h2>,
            table: ({ children }) => (
              <div className="document-table" role="region" aria-label="Plan table" tabIndex={0}>
                <table>{children}</table>
              </div>
            ),
          }}
        >
          {body.join("\n")}
        </ReactMarkdown>
      </article>
    </div>
  );
}
