from fastapi import Request, APIRouter
from schemas.esp_mesh import Meshmessage

router  =  APIRouter()
messages = []
@router.post('/api/messages')
async def receive_messages(msg : Meshmessage):
    messages.append(msg)
    print(f'Received from {msg.node_id}: {msg.message}')



@router.get('/api/messages')
async def get_messages():
    return messages 
