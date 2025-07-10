from typing import List
from pydantic import BaseModel

class Meshmessage(BaseModel):
    node_id : int
    message : str


