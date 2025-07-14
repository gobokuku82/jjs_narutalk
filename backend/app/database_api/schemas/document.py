from pydantic import BaseModel

class DocumentMeta(BaseModel):
    title: str
    description: str = ""
    s3_url: str 