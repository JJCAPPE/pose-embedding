import ReactMarkdown from "react-markdown";

export function MarkdownText({ children }: { children: string }) {
  return (
    <div className="markdown-text">
      <ReactMarkdown
        components={{
          a: ({ href, children: linkChildren }) => (
            <a href={href} rel="noreferrer" target="_blank">
              {linkChildren}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
