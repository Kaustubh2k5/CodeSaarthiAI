from pydantic import BaseModel
from typing import List

class Symbol(BaseModel):
    id: str
    name: str
    type: str
    file: str
    language: str

    imports: List[str] = []
    calls: List[str] = []

    framework_tags: List[str] = []
    description: str = ""