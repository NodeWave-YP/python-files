from pydantic import BaseModel

class Command(BaseModel):
    cmd: str
    target: str  # Could be a node ID or MAC