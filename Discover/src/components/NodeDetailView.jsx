import ReactMarkdown from "react-markdown";

export default function NodeDetailView({ node }) {
  if (!node) return null;

  return (
    <div className="thin-scroll h-full w-full overflow-y-auto px-6 py-8 sm:px-10 sm:py-10">
      <article className="prose-invert mx-auto max-w-2xl text-left leading-relaxed text-white/85 [&_a]:text-gold [&_code]:rounded [&_code]:bg-white/10 [&_code]:px-1 [&_code]:py-0.5 [&_h1]:mb-4 [&_h1]:text-2xl [&_h1]:font-bold [&_h1]:text-white [&_h2]:mt-6 [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_p]:mb-3 [&_strong]:text-white">
        <ReactMarkdown>{node.content ?? "*No content found for this node.*"}</ReactMarkdown>
      </article>
    </div>
  );
}
