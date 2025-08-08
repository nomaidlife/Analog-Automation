import os, pandas as pd, datetime, json, io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
from dotenv import load_dotenv
from app.models import SearchRequest, SearchResponse, CandidateOut, NLRequest, NLResponse, ApprovalOut, TrialOut, TrialEndpointOut
from app.scoring import score_candidate, DEFAULT_WEIGHTS
from app.utils import normalize_text, build_gazetteer, fuzzy_lookup
from app.routers import literature as literature_router
from app.security import SecurityHeadersMiddleware
load_dotenv()
app = FastAPI(title="Analog Generator — v4", version="0.6.0")
origins = ["http://localhost:3000", "https://*.vercel.app", "https://secret.nomaid.life", "https://secretapi.nomaid.life"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
CSP = "default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https:; script-src 'self' https:; connect-src 'self' https://secretapi.nomaid.life https://*.vercel.app http://localhost:8000; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
app.add_middleware(SecurityHeadersMiddleware, csp=CSP, max_body_bytes=int(os.getenv("MAX_BODY_BYTES","1048576")))
app.include_router(literature_router.router)
DATA_DIR = os.getenv("DATA_DIR","data")
def load_csv(name): return pd.read_csv(os.path.join(DATA_DIR, name))
DF_P = load_csv("analog_products.csv")
if "us_approval_date" in DF_P.columns:
    DF_P["us_approval_year"] = pd.to_datetime(DF_P["us_approval_date"], errors="coerce").dt.year
DF_A = load_csv("approvals.csv"); DF_T = load_csv("trials.csv"); DF_E = load_csv("trial_endpoints.csv"); DF_S = load_csv("synonyms.csv")
GAZ, SYN_MAP = build_gazetteer(DF_P, DF_S)
@app.get("/health")
def health(): return {"ok": True}
def seed_from_df(df, brand=None, indication=None) -> Dict[str, Any]:
    if brand: row = df[df["brand_name"].str.lower()==brand.lower()]
    elif indication: row = df[df["original_indication"].str.lower()==indication.lower()]
    else: row = df.head(0)
    if row.empty: raise HTTPException(status_code=404, detail="Seed not found.")
    r = row.iloc[0].to_dict()
    return {"brand_name": r.get("brand_name"), "ta": r.get("ta"), "ta_parent": r.get("ta_parent"), "route": r.get("route"),
            "is_biologic": bool(r.get("is_biologic")) if pd.notna(r.get("is_biologic")) else None,
            "chronic_use": bool(r.get("chronic_use")) if pd.notna(r.get("chronic_use")) else None,
            "us_approval_year": int(r.get("us_approval_year")) if pd.notna(r.get("us_approval_year")) else None,
            "entry_rank": int(r.get("entry_rank")) if pd.notna(r.get("entry_rank")) else None,
            "original_indication": r.get("original_indication"),
            "original_prev": int(r.get("original_prev")) if pd.notna(r.get("original_prev")) else None,
            "has_expansions": bool(r.get("has_expansions")) if pd.notna(r.get("has_expansions")) else None,
            "product_id": int(r.get("product_id")) if pd.notna(r.get("product_id")) else None}
def _search_core(req: SearchRequest):
    seed = seed_from_df(DF_P, brand=req.query.drug_name, indication=req.query.indication)
    f = req.filters; year_now = datetime.datetime.now().year
    df = DF_P.copy()
    if f.last_n_years and f.last_n_years>0: df = df[df["us_approval_year"] >= year_now - f.last_n_years]
    if f.exclude_oncology: df = df[df["ta"].str.lower() != "oncology"]
    if f.route_exact and seed.get("route"): df = df[df["route"].str.lower() == seed["route"].lower()]
    if f.chronic_only: df = df[df["chronic_use"] == True]
    if f.ta_include: df = df[df["ta"].isin(f.ta_include)]
    results = []
    for _, r in df.iterrows():
        if r.get("brand_name") and r.get("brand_name").lower() == str(seed.get("brand_name","")).lower(): continue
        cand = r.to_dict()
        s, partials = score_candidate(seed, cand, DEFAULT_WEIGHTS, year_now, f.last_n_years)
        piv = None
        pid = int(cand.get("product_id")) if pd.notna(cand.get("product_id")) else None
        if pid:
            t_rows = DF_T[(DF_T["product_id"]==pid) & (DF_T["is_pivotal"]==True)]
            if not t_rows.empty:
                t = t_rows.iloc[0]; e_rows = DF_E[DF_E["trial_id"]==int(t["trial_id"])]
                keyp = e_rows[e_rows["endpoint_type"]=="primary"]
                keyp = keyp.iloc[0] if not keyp.empty else None
                if keyp is not None:
                    piv = {"nct_id": t.get("nct_id"), "primary_endpoint": keyp.get("endpoint_desc"), "success": bool(keyp.get("success")) if not pd.isna(keyp.get("success")) else None, "key_p_value": keyp.get("p_value"), "source_url": keyp.get("source_url")}
        results.append(CandidateOut(product_id=pid, brand_name=cand.get("brand_name",""), manufacturer=cand.get("manufacturer"),
            us_approval_year=int(cand.get("us_approval_year")) if pd.notna(cand.get("us_approval_year")) else None, ta=cand.get("ta"), route=cand.get("route"),
            is_biologic=bool(cand.get("is_biologic")) if pd.notna(cand.get("is_biologic")) else None, chronic_use=bool(cand.get("chronic_use")) if pd.notna(cand.get("chronic_use")) else None,
            entry_rank=int(cand.get("entry_rank")) if pd.notna(cand.get("entry_rank")) else None, original_indication=cand.get("original_indication"),
            original_prev=int(cand.get("original_prev")) if pd.notna(cand.get("original_prev")) else None, expansions=cand.get("expansions_list"), score=float(s), partials=partials, pivotal_summary=piv))
    results.sort(key=lambda x: x.score, reverse=True); return seed, results
@app.post("/analogs/search", response_model=SearchResponse)
def analogs_search(req: SearchRequest): seed, results = _search_core(req); return SearchResponse(seed=seed, results=results[:req.limit], meta={"count": len(results)})
@app.post("/export")
def export_csv(req: SearchRequest):
    seed, results = _search_core(req); import csv
    output = io.StringIO(); w = csv.writer(output)
    w.writerow(["brand_name","product_id","us_approval_year","ta","route","chronic_use","entry_rank","score","primary_endpoint","p_value","nct_id"])
    for r in results[:req.limit]:
        piv = r.pivotal_summary or {}
        w.writerow([r.brand_name, r.product_id or "", r.us_approval_year or "", r.ta or "", r.route or "", "Yes" if r.chronic_use else "No", r.entry_rank or "", f"{r.score:.4f}", piv.get("primary_endpoint",""), piv.get("key_p_value",""), piv.get("nct_id","")])
    output.seek(0); return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=analogs.csv"})
@app.post("/nl2search", response_model=NLResponse)
def nl2search(payload: NLRequest):
    q = normalize_text(payload.query); notes = []
    canon, score = fuzzy_lookup(q, {k.lower():v for k,v in GAZ.items()})
    candidates = None; drug=None; indication=None
    if canon:
        if canon in DF_P['original_indication'].astype(str).tolist(): indication = canon
        elif canon in DF_P['brand_name'].astype(str).tolist(): drug = canon
        else: candidates = list(DF_P['brand_name'].dropna().unique()[:5])
    sr = {"query": {"drug_name": drug, "indication": indication}, "filters": {"last_n_years": 5, "exclude_oncology": True, "route_exact": False, "chronic_only": False, "ta_include": None, "approval_market": "US"}, "limit": 10}
    return NLResponse(structured=sr, notes="NL parsed", candidates=candidates)
