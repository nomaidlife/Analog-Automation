import os, time, requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from app.utils import cache_key
CTGOV_BASE="https://clinicaltrials.gov/api/v2"; HEADERS={"User-Agent": os.getenv("POLITE_AGENT","namaid-analog/1.0 (contact: admin@nomaid.life)")}
class RateLimit(Exception): pass
@retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential_jitter(1,8), retry=retry_if_exception_type((requests.RequestException, RateLimit)))
def get(path:str, params:dict|None=None, etag_cache:dict|None=None):
    url=f"{CTGOV_BASE}{path}"; headers=dict(HEADERS); ck=cache_key(url, params or {})
    if etag_cache and ck in etag_cache: headers["If-None-Match"]=etag_cache[ck].get("etag","")
    resp=requests.get(url, params=params, headers=headers, timeout=30)
    if resp.status_code==304: return {"cached":True,"data":etag_cache[ck]["data"]}
    if resp.status_code==429: raise RateLimit("rate-limited")
    resp.raise_for_status(); data=resp.json()
    if etag_cache is not None: etag_cache[ck]={"etag": resp.headers.get("ETag",""), "data": data}
    return {"cached":False,"data":data}
def search_studies(query:str, page_size:int=100, etag_cache=None):
    token=None
    while True:
        params={"query.term": query, "pageSize": page_size}
        if token: params["pageToken"]=token
        res=get("/studies", params=params, etag_cache=etag_cache)
        studies=res["data"].get("studies", [])
        if not studies: break
        yield studies
        token=res["data"].get("nextPageToken")
        if not token: break
        time.sleep(float(os.getenv("CTGOV_THROTTLE","0.25")))
