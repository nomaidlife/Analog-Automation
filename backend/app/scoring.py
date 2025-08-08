from math import log
from typing import Optional
def route_similarity(a,b): 
    if not a or not b: return 0.5
    a,b=a.lower(),b.lower()
    if a==b: return 1.0
    return 0.5 if (a,b) in {("oral","iv"),("iv","oral"),("sc","im"),("im","sc"),("topical","transdermal"),("transdermal","topical")} else 0.0
def recency_boost(year,last_n,current):
    if last_n<=0 or not year: return 1.0
    age=current-int(year); return max(0.0, 1.0-(age/last_n))
def prevalence_similarity(ps,pc):
    try:
        if not ps or not pc or ps<=0 or pc<=0: return 0.5
        from math import log; dist=abs(log(ps)-log(pc)); return 1-min(1, dist/3.0)
    except: return 0.5
def entry_order_similarity(rs,rc):
    try: 
        from builtins import abs
        return 1.0/(1.0+abs(int(rs)-int(rc)))
    except: return 0.5
DEFAULT_WEIGHTS={"ta":0.20,"modality":0.15,"route":0.15,"chronic":0.15,"recency":0.10,"entry":0.10,"prev":0.10,"expand":0.05}
def score_components(seed,cand,current,last_n):
    ta=1.0 if cand.get("ta")==seed.get("ta") else (0.5 if cand.get("ta_parent")==seed.get("ta_parent") else 0.0)
    mod=1.0 if cand.get("is_biologic")==seed.get("is_biologic") else 0.0
    route=route_similarity(cand.get("route"),seed.get("route"))
    chronic=1.0 if cand.get("chronic_use")==seed.get("chronic_use") else 0.0
    rec=recency_boost(cand.get("us_approval_year"), last_n, current)
    entry=entry_order_similarity(seed.get("entry_rank"), cand.get("entry_rank"))
    prev=prevalence_similarity(seed.get("original_prev"), cand.get("original_prev"))
    exp=1.0 if cand.get("has_expansions")==seed.get("has_expansions") else 0.0
    return {"ta":ta,"modality":mod,"route":route,"chronic":chronic,"recency":rec,"entry":entry,"prev":prev,"expand":exp}
def score_with_weights(components,weights): return sum(weights.get(k,0.0)*components.get(k,0.0) for k in DEFAULT_WEIGHTS)
def score_candidate(seed,cand,weights,current,last_n):
    comp=score_components(seed,cand,current,last_n); w=weights or DEFAULT_WEIGHTS
    score=score_with_weights(comp,w); partials={k:w.get(k,0.0)*comp[k] for k in comp}
    return float(score), partials
