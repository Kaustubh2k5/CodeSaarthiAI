from pydantic import BaseModel
from typing import List


class DescriptionOutput(BaseModel):
    description: str
    tags: List[str]