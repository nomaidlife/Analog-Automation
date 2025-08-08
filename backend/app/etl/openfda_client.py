import os, time, requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from app.utils import cache_key
OPENFDA_BASE="https://api.fda.gov"; HEADERS={"User-Agent": os.getenv("POLITE_AGENT","namaid-analog/1.0 (contact: admin@nomaid.life)")}
API_KEY=os.getenv("OPENFDA_API_KEY")
class RateLimit(Exception): pass
def _params(params:dict|None=None):
    p=dict(params or {}); 
    if API_KEY: p["api_key"]=API_KEY
    return p
@retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential_jitter(1,8), retry=retry_if_exception_type((requests.RequestException, RateLimit)))
def get(path:str, params:dict|None=None, etag_cache:dict|None=None):
    url=f"{OPENFDA_BASE}{path}"; p=_params(params); headers=dict(HEADERS); ck=cache_key(url,p)
    if etag_cache and ck in etag_cache: headers["If-None-Match"]=etag_cache[ck].get("etag","")
    resp=requests.get(url, params=p, headers=headers, timeout=30)
    if resp.status_code==304: return {"cached":True,"data":etag_cache[ck]["data"]}
    if resp.status_code==429: raise RateLimit("rate-limited")
    resp.raise_for_status(); data=resp.json()
    if etag_cache is not None: etag_cache[ck]={"etag": resp.headers.get("ETag",""), "data": data}
    return {"cached":False,"data":data}
def iterate_drugsfda(limit=500, etag_cache=None):
    # this endpoint supports skip/limit
    skip=0
    while True:
        res=get("/drug/drugsfda.json", params={"limit": min(100, limit), "skip": skip}, etag_cache=etag_cache)
        results=res["data"].get("results", [])
        if not results: break
        yield results; skip+=len(results); time.sleep(float(os.getenv("OPENFDA_THROTTLE","0.25")))
