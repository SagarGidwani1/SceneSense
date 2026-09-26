from pydantic import BaseModel, Field
from typing import List


class Brand(BaseModel):
    brand_id: str
    brand_name: str
    category: str
    description: str = ""
    positive_contexts: List[str] = Field(default_factory=list)
    negative_contexts: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    creative_url: str = ""  # optional; a synthetic creative is generated when empty


class BrandCatalog(BaseModel):
    brands: List[Brand] = Field(default_factory=list)
