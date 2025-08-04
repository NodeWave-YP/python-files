from fastapi import APIRouter, Request
from schemas.mqtt_schema import Command
from services.mqtt__publisher import publish_command

router = APIRouter()


@router.post("/send-command", tags=["mqtt"])
async def send_command(command: Command):
    """
    Send a command from backend to ESP nodes via /mesh/commands topic
    """
    publish_command(command.dict())
    return {"message": "Command sent successfully"}
