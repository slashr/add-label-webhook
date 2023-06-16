from pydantic import BaseModel

class Patch(BaseModel):
    op: str
    path: str = "/metadata/labels"
    value: dict[str, str]
