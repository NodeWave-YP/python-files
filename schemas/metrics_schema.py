from pydantic import BaseModel



class Metrics(BaseModel):
    signal_strength : float
    latency : float
    data_usage : float
    mac_address:  str