from fastapi import FastAPI, APIRouter, HTTPException,status, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from schemas.user_schema import User
from  hash import hashed
from services.supabase_client import supabase

router = APIRouter()
template = Jinja2Templates(directory='template')

@router.get("/")
async def login_form(request: Request):
    return template.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_model=None)
async def login_form(request: Request, username: str = Form(...), password: str = Form(...)):
    response = supabase.table("user_accounts").select("*").eq("username", username).single().execute()

    if not response.data:
        return template.TemplateResponse("login.html", {"request": request, "error": "Invalid username"})

    user = response.data
    if not hashed.verify(password, user["password_hash"]):
        return template.TemplateResponse("login.html", {"request": request, "error": "Incorrect password"})

    return RedirectResponse("/dashboard", status_code=302)

# JSON-based login endpoint
# @router.post("/api/login", tags=["auth"], response_model=None)
# async def api_login(user: User):
#     result = supabase.table("user_accounts").select("*").eq("username", user.username).single().execute()

#     if not result.data:
#         raise HTTPException(status_code=404, detail='Username not found')

#     if hashed.verify(user.password, result.data["password_hash"]):
#         return {"message": "Successful login"}

#     raise HTTPException(status_code=401, detail="Incorrect username or password")


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
    node_lookup = supabase.table("node").select("node_id").eq("mac_address", node_mac).single().execute()
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

# JSON-based register endpoint
# @router.post("/api/register", tags=["auth"])
# async def api_register(user: User):
#     node_lookup = supabase.table("node").select("node_id").eq("mac_address", user.node_mac).single().execute()
#     if not node_lookup.data:
#         raise HTTPException(status_code=400, detail="Node not recognized")
    
#     node_id = node_lookup.data["node_id"]
#     supabase.table("user_accounts").insert({
#         "username": user.username,
#         "password_hash": hashed.hash(user.password),
#         "node_id": node_id,
#         "role": "user"
#     }).execute()

#     return {"message": "User registered successfully"}

