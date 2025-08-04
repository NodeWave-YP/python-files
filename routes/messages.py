from fastapi import Request, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from schemas.esp_mesh import Meshmessage
import secrets
import os
from dotenv import load_dotenv
router = APIRouter()
security = HTTPBasic()


load_dotenv()

VALID_USERNAME = os.getenv("BACKEND_UNAME")
VALID_PASSWORD = os.getenv("BACKEND_PASSWORD")

messages = []

# Authentication function
def authenticate_device(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, VALID_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, VALID_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

@router.post("/api/messages")
async def receive_messages(msg: Meshmessage, _: str = Depends(authenticate_device)):
    messages.append(msg)
    print(f"Received from {msg.node_id}: {msg.message}")
    return {"message": "Message received successfully"}

@router.get("/api/messages")
async def get_messages(_: str = Depends(authenticate_device)):
    return messages
