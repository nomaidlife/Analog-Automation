from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
class SearchFilters(BaseModel):
    last_n_years:int=5; exclude_oncology:bool=True; route_exact:bool=False; chronic_only:bool=False; ta_include:Optional[List[str]]=None; approval_market:str="US"
class QueryInput(BaseModel): drug_name:Optional[str]=None; indication:Optional[str]=None
class SearchRequest(BaseModel): query:QueryInput; filters:SearchFilters=SearchFilters(); limit:int=10
class CandidateOut(BaseModel):
    product_id:Optional[int]=None; brand_name:str; manufacturer:Optional[str]=None; us_approval_year:Optional[int]=None; ta:Optional[str]=None; route:Optional[str]=None
    is_biologic:Optional[bool]=None; chronic_use:Optional[bool]=None; entry_rank:Optional[int]=None; original_indication:Optional[str]=None; original_prev:Optional[int]=None
    expansions:Optional[str]=None; score:float; partials:Dict[str,float]; pivotal_summary:Optional[Dict[str,Any]]=None
class SearchResponse(BaseModel): seed:Dict[str,Any]; results:List[CandidateOut]; meta:Dict[str,Any]=Field(default_factory=dict)
class NLRequest(BaseModel): query:str
class NLResponse(BaseModel): structured:SearchRequest; notes:str; candidates:Optional[List[str]]=None
class ApprovalOut(BaseModel): approval_id:int; app_type:str; app_number:str; action_date:Optional[str]=None; review_designation:Optional[str]=None; doc_urls:Dict[str,str]=Field(default_factory=dict)
class TrialEndpointOut(BaseModel):
    trial_id:int; endpoint_type:str; endpoint_desc:str; statistical_method:Optional[str]=None; effect_size:Optional[str]=None; p_value:Optional[str]=None; ci:Optional[str]=None; success:Optional[bool]=None; source:Optional[str]=None; source_url:Optional[str]=None
class TrialOut(BaseModel):
    trial_id:int; product_id:int; approval_id:Optional[int]=None; nct_id:Optional[str]=None; name:Optional[str]=None; phase:Optional[str]=None; design:Optional[str]=None; population_key:Optional[str]=None; sample_size:Optional[int]=None; primary_completion_date:Optional[str]=None; is_pivotal:Optional[bool]=None; endpoints:List[TrialEndpointOut]=Field(default_factory=list)
class FeedbackIn(BaseModel): seed:str; product_id:int; label:str; note:Optional[str]=None
class FeedbackSummary(BaseModel): total:int; positives:int; negatives:int; items:List[Dict[str,Any]]
class WeightsProposal(BaseModel): weights:Dict[str,float]; rationale:str
class LitSearchRequest(BaseModel): indication:str; ta:Optional[str]=None; limit:int=10
class LiteratureOut(BaseModel):
    lit_id:int; title:str; year:Optional[int]=None; doi:Optional[str]=None; pmid:Optional[str]=None; venue:Optional[str]=None; is_guideline:bool=False; url:Optional[str]=None; oa_url:Optional[str]=None; ta:Optional[str]=None; cited_by_count:Optional[int]=None; ref_count:Optional[int]=None; evidence_type:Optional[str]=None; score:float
class OrgResource(BaseModel): org_id:int; name:str; type:str; url:str; page_url:Optional[str]=None; page_type:Optional[str]=None
class OrgResourcesResponse(BaseModel): items:List[OrgResource]
class PrevalenceRef(BaseModel): source:str; url:Optional[str]=None; year:Optional[int]=None; value:Optional[str]=None; notes:Optional[str]=None
class PrevalenceResponse(BaseModel): indication:str; items:List[PrevalenceRef]
