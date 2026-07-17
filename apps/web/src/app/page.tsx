import { resolveApiBaseUrl } from "@lhf/api-client";

export default function Home() {
  const apiBaseUrl = resolveApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);

  return (
    <main>
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Local research workspace</p>
        <h1 id="page-title">
          Find a London home with the evidence in one place.
        </h1>
        <p className="lede">
          Compare collected listings, neighbourhood details, and the trade-offs
          that matter before arranging a viewing.
        </p>
        <p className="status">
          API connection: <code>{apiBaseUrl}</code>
        </p>
      </section>
    </main>
  );
}
