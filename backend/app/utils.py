from rapidfuzz import process, fuzz
import pandas as pd, json, os, datetime, hashlib
def normalize_text(s:str)->str: return (s or "").strip().lower()
def build_gazetteer(df_products: pd.DataFrame, df_syn: pd.DataFrame):
    names=set(df_products['brand_name'].dropna().astype(str))|set(df_products['generic_name'].dropna().astype(str))|set(df_products['original_indication'].dropna().astype(str))
    syn_map={row['from']:row['to'] for _,row in df_syn.iterrows()}; return {n:n for n in names}, syn_map
def fuzzy_lookup(query:str,candidates):
    choices=list(candidates.keys()); match,score,_=process.extractOne(query, choices, scorer=fuzz.WRatio); return candidates.get(match), score/100.0
def append_jsonl(path:str,obj:dict):
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path,"a",encoding="utf-8").write(json.dumps(obj,ensure_ascii=False)+"
")
def read_jsonl(path:str):
    if not os.path.exists(path): return []
    return [json.loads(l) for l in open(path,encoding="utf-8") if l.strip()]
def now_iso(): return datetime.datetime.utcnow().isoformat()+"Z"
def cache_key(url:str,params:dict|None)->str:
    raw=url+"?"+json.dumps(params or {}, sort_keys=True); return hashlib.sha256(raw.encode()).hexdigest()
