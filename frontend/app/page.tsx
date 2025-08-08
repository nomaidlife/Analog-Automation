"use client";

import React, { useState } from "react";

// Read from Vercel env; fall back to your live API
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "https://secretapi.nomaid.life";

type Candidate = {
  product_id?: number;
  brand_name: string;
  us_approval_year?: number;
  ta?: string;
  route?: string;
  score: number;
};

export default function Page() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<{ results?: Candidate[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleSearch() {
    setLoading(true);
    setErr(null);
    setResults(null);
    try {
      // 1) NL → structured
      const nlRes = await fetch(`${BACKEND_URL}/nl2search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!nlRes.ok) throw new Error(`nl2search ${nlRes.status}`);
      const { structured } = await nlRes.json();

      // 2) structured → analogs
      const analogRes = await fetch(`${BACKEND_URL}/analogs/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(structured),
      });
      if (!analogRes.ok) throw new Error(`analogs/search ${analogRes.status}`);
      const data = await analogRes.json();
      setResults(data);
    } catch (e: any) {
      console.error(e);
      setErr(e?.message || "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Analog Generator</h1>
      <div className="text-xs text-gray-500">
        API: <code>{BACKEND_URL}</code>
      </div>

      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a brand/generic/indication (e.g., PAH, Opsynvi, gMG)"
          className="w-full px-4 py-3 rounded-2xl border focus:outline-none"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="inline-flex items-center justify-center rounded-2xl font-medium transition disabled:opacity-50 bg-black text-white hover:opacity-90 px-4 py-2 text-sm"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {err ? (
        <div className="text-sm text-red-600 border border-red-200 rounded-2xl p-3">
          {err}
        </div>
      ) : null}

      <div className="rounded-2xl border overflow-hidden">
        {results?.results && results.results.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr>
                <th className="p-2 text-left">Asset</th>
                <th className="p-2 text-left">Year</th>
                <th className="p-2 text-left">TA</th>
                <th className="p-2 text-left">Route</th>
                <th className="p-2 text-left">Score</th>
              </tr>
            </thead>
            <tbody>
              {results.results.map((r) => (
                <tr key={`${r.brand_name}-${r.product_id ?? ""}`} className="border-t">
                  <td className="p-2">{r.brand_name}</td>
                  <td className="p-2">{r.us_approval_year ?? "—"}</td>
                  <td className="p-2">{r.ta ?? "—"}</td>
                  <td className="p-2">{r.route ?? "—"}</td>
                  <td className="p-2">{(r.score * 100).toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-6 text-sm text-gray-500">No results yet.</div>
        )}
      </div>
    </div>
  );
}
