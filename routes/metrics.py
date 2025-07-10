from fastapi import status, APIRouter, HTTPException, FastAPI
from schemas.metrics_schema import Metrics
from services.supabase_client import supabase




router = APIRouter()


router.post('/metrics', status_code=status.HTTP_200_OK)
async def receive_metrics(metrics: Metrics):
    result = supabase.table('node').eq('mac_address', metrics.mac_address).single().execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Device not available')
    

    node_id = result.data[0]['node_id']

    supabase.table('performance_metrics').insert({
        'node_id' : node_id,
        'signal_strength' : metrics.signal_strength,
        'latency' :  metrics.latency,
        'data_usage': metrics.data_usage
    }).execute()
    
    return {'message': 'Sucessful'}