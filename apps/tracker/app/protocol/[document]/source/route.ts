import { isProtocolDocumentName, protocolDocuments } from "@/lib/protocol-documents";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ document: string }> },
) {
  const { document } = await params;
  if (!isProtocolDocumentName(document)) return new Response("Not found", { status: 404 });
  const source = protocolDocuments[document];
  return new Response(source.markdown, {
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": `attachment; filename="${source.filename}"`,
      "X-Content-Type-Options": "nosniff",
    },
  });
}
