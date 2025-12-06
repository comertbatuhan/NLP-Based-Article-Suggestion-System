from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class WorksSearchRequest(BaseModel):
    keywords: Optional[List[str]] = Field(
        None,
        description="List of keywords to search in title and abstract."
    )
    abstracts: Optional[List[str]] = Field(
        None,
        description="List of terms to search in abstract only."
    )
    start_date: Optional[str] = Field(
        None,
        description="Start publication date in YYYY-MM-DD format."
    )
    end_date: Optional[str] = Field(
        None,
        description="End publication date in YYYY-MM-DD format."
    )

    
class WorkSummary(BaseModel):
    id: str
    title: str
    keywords: str
    abstract: str
    publication_year: Optional[int]

class WorksSearchResponse(BaseModel):
    results: List[WorkSummary]
