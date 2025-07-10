from fastapi import FastAPI, APIRouter, HTTPException,status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse,JSONResponse
from schemas.user_schema import User
from  hash import hashed
from services.supabase_client import supabase
import services.oauth as sva

router = APIRouter()
template = Jinja2Templates(directory='template')

@router.get("/")
async def login_form(request: Request):
    return template.TemplateResponse("login.html", {"request": request})


@router.post("/login", tags=['auth'],response_model=None)
async def login_form(request: Request, username: str = Form(...), password: str = Form(...)):
    response = supabase.table("user_accounts").select("*").eq("username", username).limit(1).execute()

    if not response.data:
        return template.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    user = response.data[0]  # It's a dict

    if not hashed.verify(password, user["password_hash"]):
        return template.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    # ✅ Create token properly using user["role"]
    token = sva.create_access_token({"username": user["username"], "role": user["role"]})

    # ✅ You can't return JSON and Redirect at the same time
    # If this is a FORM login, return a redirect (not JSON)
    # You can store token in cookie or session later if needed

    return RedirectResponse("/dashboard", status_code=302)


@router.get("/register", response_model=None)
def register_page(request: Request):
    return template.TemplateResponse("register.html", {"request": request})

# Web form (POST)
@router.post("/register", response_model=None)
async def register_form(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    node_mac: str = Form(...)
    
):
    node_lookup = supabase.table("node").select("node_id").eq("mac_address", node_mac).limit(1).execute()
    if not node_lookup.data:
        return template.TemplateResponse("register.html", {"request": request, "error": "Unknown node"})
    
    node_id = node_lookup.data["node_id"]
    supabase.table("user_accounts").insert({
        "username": username,
        "password_hash": hashed.hash(password),
        "node_id": node_id,
        "role": "user"
    }).execute()

    return RedirectResponse("/login", status_code=302)

#JSON-based register endpoint
@router.post("/api/register", tags=["auth"])
async def api_register(user: User):
    node_lookup = supabase.table("node").select("node_id").eq("mac_address", user.node_mac).limit(1).execute()
    if not node_lookup.data:
        raise HTTPException(status_code=400, detail="Node not recognized")
    
    node_id = node_lookup.data["node_id"]
    supabase.table("user_accounts").insert({
        "username": user.username,
        "password_hash": hashed.hash(user.password),
        "node_id": node_id,
        "role": "user"
    }).execute()

    return {"message": "User registered successfully"}


# JSON-based login endpoint
@router.post("/api/login", tags=["auth"], response_model=None)
async def api_login(user: User):
    result = supabase.table("user_accounts").select("*").eq("username", user.username).limit(1).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail='Username not found')

    if hashed.verify(user.password, result.data["password_hash"]):
        return {"message": "Successful login"}

    raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = sva.create_access_token({"username": user.username, "role": result.data["role"]})

    return JSONResponse({"access_token": token, "token_type": "bearer"})
