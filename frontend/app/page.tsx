"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// Use env var in Vercel; fall back to your live API
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "https://secretapi.nomaid.life";

type Candidate = {
  product_id?: number;
  brand_name: string;
  us_approval_year?: number;
  ta?: string;
  route?: string;
  chronic_use?: boolean;
  entry_rank?: number;
  score: number;
  partials?: any;
  pivotal_summary?: any;
};

export default function Page() {
  const [q, setQ] = useState("");
  const [data, setData] = useState<{ results?: Candidate[] } | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    setData(null);
    try {
      // Step 1: natural-language → structured search
      const nl = await fetch(`${BACKEND_URL}/nl2search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q }),
      }).then((r) => {
        if (!r.ok) throw new Error(`nl2search ${r.status}`);
        return r.json();
      });

      // Step 2: search analogs with the structured payload
      const res = await fetch(`${BACKEND_URL}/analogs/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nl.structured),
      }).then((r) => {
        if (!r.ok) throw new Error(`analogs/search ${r.status}`);
        return r.json();
      });

      setData(res);
    } catch (e: any) {
      setErr(e?.message || "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Analog Generator</h1>

      {/* tiny debug note so we know which API the UI is calling */}
      <div className="text-xs text-gray-500">
        API: <code>{BACKEND_URL}</code>
      </div>

      <div className="flex gap-2">
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Type a brand/generic/indication (e.g., PAH, Opsynvi, gMG)"
        />
        <Button onClick={run} disabled={loading}>
          {loading ? "Searching…" : "Search"}
        </Button>
      </div>

      {err ? (
        <div className="text-sm text-red-600 border border-red-200 rounded-2xl p-3">
          {err}
        </div>
      ) : null}

      <div className="rounded-2xl border overflow-hidden">
        {data?.results && data.results.length > 0 ? (
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
              {data.results.map((r) => (
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
