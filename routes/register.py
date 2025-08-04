from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from services.database import get_sqlite_db
from models import Users, Devices, Node
from utils.mac_lookup import get_mac_address
from utils.hashing import hashed
from utils.validation import validate_username, validate_password
from user_schema import User

import logging


logger = logging.getLogger(__name__)
template = Jinja2Templates(directory="templates")

router = APIRouter()

#=======Web Interface=========
@router.get("/")
async def home_page(request: Request):
    return RedirectResponse(url="/index")

@router.get("/index", response_class=HTMLResponse)
async def show_home_page(request: Request):
    return template.TemplateResponse("index.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, error: Optional[str] = None, success: Optional[str] = None):
    client_ip = request.client.host
    mac_address = get_mac_address(client_ip)

    context = {
        "request": request,
        "mac_address": mac_address,
        "node_available": mac_address is not None
    }
    if error:
        context["error"] = error
    if success:
        context["success"] = success

    return template.TemplateResponse("register.html", context)

@router.post("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_sqlite_db)
):
    client_ip = request.client.host
    mac_address = get_mac_address(client_ip)
    logger.info(f"Registration attempt from IP {client_ip}, MAC: {mac_address}")

    errors = []
    username_valid, username_error = validate_username(username)
    if not username_valid:
        errors.append(username_error)

    password_valid, password_error = validate_password(password)
    if not password_valid:
        errors.append(password_error)

    if password != confirm_password:
        errors.append("Passwords do not match")

    if not mac_address:
        errors.append("Could not determine MAC address")

    if errors:
        return template.TemplateResponse("register.html", {
            "request": request,
            "error": ". ".join(errors),
            "username": username,
            "mac_address": mac_address,
            "node_available": False
        })

    # Clean username
    username = username.strip().lower()

    # Check for existing user
    user_exists = db.query(Users).filter_by(username=username).first()
    if user_exists:
        return template.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already exists",
            "mac_address": mac_address,
            "node_available": True
        })

    # Assign node by MAC prefix match
    node = db.query(Node).filter(Node.mac_address.startswith(mac_address[:8])).first()
    if not node:
        return template.TemplateResponse("register.html", {
            "request": request,
            "error": "No matching node found for this MAC address",
            "mac_address": mac_address,
            "node_available": False
        })

    try:
        new_user = Users(username=username, password_hash=hashed.hash(password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        new_device = Devices(user_id=new_user.user_id, node_id=node.node_id, mac_address=mac_address)
        db.add(new_device)
        db.commit()

        return RedirectResponse(url="/login?success=Registration successful! Please log in.", status_code=HTTP_302_FOUND)

    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        db.rollback()
        return template.TemplateResponse("register.html", {
            "request": request,
            "error": "Registration failed. Try again later.",
            "mac_address": mac_address,
            "username": username,
            "node_available": True
        })

