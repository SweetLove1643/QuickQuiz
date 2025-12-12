from pydantic import BaseModel

class SummaryRequestModel(BaseModel):
    text: str