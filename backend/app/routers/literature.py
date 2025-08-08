import os, pandas as pd
from fastapi import APIRouter
from app.models import LitSearchRequest, LiteratureOut, OrgResource, OrgResourcesResponse, PrevalenceRef, PrevalenceResponse
router=APIRouter(prefix="", tags=["literature"])
DATA_DIR=os.getenv("DATA_DIR","data")
def load_csv(name): return pd.read_csv(os.path.join(DATA_DIR,name))
DF_L=DF_AU=DF_LA=DF_ORG=DF_ORGP=None
def _ensure():
    global DF_L,DF_AU,DF_LA,DF_ORG,DF_ORGP
    if DF_L is None:
        DF_L=load_csv("literature.csv"); DF_AU=load_csv("authors.csv"); DF_LA=load_csv("lit_authors.csv"); DF_ORG=load_csv("orgs.csv"); DF_ORGP=load_csv("org_pages.csv")
@router.post("/literature/search", response_model=list[LiteratureOut])
def literature_search(req: LitSearchRequest):
    _ensure(); df=DF_L.copy(); rel=df["title"].str.contains(req.indication,case=False,na=False)|(df["indication_canonical"].str.lower()==req.indication.lower()); df=df[rel].head(req.limit)
    return [LiteratureOut(lit_id=int(r["lit_id"]), title=r["title"], year=int(r["year"]) if pd.notna(r["year"]) else None, doi=r.get("doi"), pmid=r.get("pmid"), venue=r.get("venue"), is_guideline=bool(r.get("is_guideline")), url=r.get("url"), oa_url=r.get("oa_url"), ta=r.get("ta"), cited_by_count=int(r["cited_by_count"]) if not pd.isna(r["cited_by_count"]) else None, ref_count=int(r["ref_count"]) if not pd.isna(r["ref_count"]) else None, evidence_type=r.get("evidence_type"), score=1.0) for _,r in df.iterrows()]
@router.get("/orgs/resources", response_model=OrgResourcesResponse)
def org_resources(ta:str|None=None, indication:str|None=None):
    _ensure(); orgs=DF_ORG.copy(); pages=DF_ORGP.copy(); merged=pages.merge(orgs,on="org_id",how="inner")
    items=[OrgResource(org_id=int(r["org_id"]), name=r["name"], type=r["type"], url=r["url_y"], page_url=r["page_url"], page_type=r["page_type"]) for _,r in merged.iterrows()]
    return OrgResourcesResponse(items=items)
@router.get("/evidence/prevalence", response_model=PrevalenceResponse)
def prevalence(indication:str):
    return PrevalenceResponse(indication=indication, items=[PrevalenceRef(source="Orphanet", url="https://www.orpha.net")])
