import os, json, pandas as pd
from app.etl import openfda_client as ofda, ctgov_client as ctg
CACHE_FILE=os.getenv("ETL_CACHE","data/cache/etag_cache.json")
def load_cache():
    if os.path.exists(CACHE_FILE):
        try: return json.load(open(CACHE_FILE))
        except Exception: return {}
    return {}
def save_cache(cache:dict):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True); json.dump(cache, open(CACHE_FILE,"w"))
def sync_openfda_drugsfda():
    cache=load_cache(); rows=[]
    for batch in ofda.iterate_drugsfda(limit=2000, etag_cache=cache):
        rows.extend(batch)
    if rows:
        os.makedirs("data/raw", exist_ok=True); pd.DataFrame(rows).to_csv("data/raw/openfda_drugsfda.csv", index=False)
    save_cache(cache); print("OpenFDA drugsfda rows:", len(rows))
def sync_ctgov(term="pulmonary arterial hypertension"):
    cache=load_cache(); rows=[]
    for studies in ctg.search_studies(term, page_size=100, etag_cache=cache):
        rows.extend(studies)
    if rows:
        os.makedirs("data/raw", exist_ok=True); pd.DataFrame(rows).to_csv("data/raw/ctgov_studies.csv", index=False)
    save_cache(cache); print("CT.gov studies:", len(rows))
if __name__=="__main__":
    sync_openfda_drugsfda(); sync_ctgov()
