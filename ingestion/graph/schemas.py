from pydantic import BaseModel, Field, field_validator
from typing import List


class EnrichmentResult(BaseModel):

    responsibility: str = Field(default="")
    keywords: List[str] = Field(default_factory=list)
    technical_summary: str = Field(default="")

    @field_validator("responsibility")
    @classmethod
    def normalize_responsibility(cls, v):
        return v.strip() if isinstance(v, str) else ""

    @field_validator("technical_summary")
    @classmethod
    def normalize_summary(cls, v):
        return v.strip()[:500] if isinstance(v, str) else ""

    @field_validator("keywords")
    @classmethod
    def normalize_keywords(cls, v):
        if not isinstance(v, list):
            return []

        cleaned = []
        for k in v:
            if isinstance(k, str):
                k = k.lower().strip()
                if k:
                    cleaned.append(k)

        return cleaned