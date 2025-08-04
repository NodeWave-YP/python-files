from fastapi import APIRouter, Request, Form, HTTPException, status, Depends
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from services.supabase_client import supabase
from hash import hashed
from services import oauth
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import re
from services.input_validation import validate_password, validate_username, get_available_node,authenticate_user,validate_login_input,create_secure_cookie_response, create_user_token,check_username_exists 
from fastapi.responses import RedirectResponse
router = APIRouter()
template = Jinja2Templates(directory='templates')
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

# Configuration
TOKEN_EXPIRE_HOURS = 24
COOKIE_SECURE = False  # Set to True in production with HTTPS
COOKIE_SAMESITE = "lax"

# Role-based routing configuration
ROLE_REDIRECTS = {
    "admin": "/admin_dashboard",
    "user": "/user_dashboard",
    "moderator": "/moderator_dashboard"  # Future-proofing for additional roles
}


# ========== WEB ROUTES ==========

@router.get("/login")
async def login_page(request: Request, success: Optional[str] = None, error: Optional[str] = None):
    """Display the login form"""
    context = {"request": request}
    
    if success:
        context["success"] = success
    if error:
        context["error"] = error
        
    return template.TemplateResponse("login.html", context)

@router.post("/login", tags=['auth'], response_model=None)
async def login_form(
    request: Request, 
    username: str = Form(...), 
    password: str = Form(...)
):
    """Process login form submission"""
    logger.info(f"Login attempt for username: {username}")
    
    # Input validation
    is_valid, validation_error = validate_login_input(username, password)
    if not is_valid:
        logger.warning(f"Login validation failed: {validation_error}")
        return template.TemplateResponse("login.html", {
            "request": request,
            "error": validation_error,
            "username": username.strip() if username else ""
        })
    
    # Authenticate user
    user, auth_error = await authenticate_user(username, password)
    if not user:
        return template.TemplateResponse("login.html", {
            "request": request,
            "error": auth_error,
            "username": username.strip()
        })
    
    try:
        # Create token
        token = create_user_token(user)
        
        # Get redirect URL based on role
        redirect_url = ROLE_REDIRECTS.get(user["role"])
        if not redirect_url:
            logger.error(f"No redirect URL configured for role: {user['role']}")
            return template.TemplateResponse("login.html", {
                "request": request,
                "error": "Access configuration error. Please contact support."
            })
        
        # Create secure response with cookie
        response = create_secure_cookie_response(redirect_url, token)
        
        logger.info(f"Successful login for user: {username}, redirecting to: {redirect_url}")
        return response
        
    except Exception as e:
        logger.error(f"Login processing error for {username}: {str(e)}")
        return template.TemplateResponse("login.html", {
            "request": request,
            "error": "Login failed. Please try again later.",
            "username": username.strip()
        })

# ========== LOGOUT ROUTES ==========

@router.post("/logout")
@router.get("/logout")
async def logout(request: Request):
    """Handle user logout (supports both GET and POST)"""
    logger.info("User logout initiated")
    
    response = RedirectResponse("/login?success=You have been logged out successfully.", status_code=302)
    
    # Clear the access token cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )
    
    logger.info("User logged out successfully")
    return response

# ========== API ROUTES ==========

@router.post("/api/login", tags=['auth'])
async def api_login(
    username: str = Form(...), 
    password: str = Form(...)
):
    """API-only login endpoint that returns JSON"""
    logger.info(f"API login attempt for username: {username}")
    
    # Input validation
    is_valid, validation_error = validate_login_input(username, password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error
        )
    
    # Authenticate user
    user, auth_error = await authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_error,
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Create token
        token = create_user_token(user)
        
        logger.info(f"Successful API login for user: {username}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": TOKEN_EXPIRE_HOURS * 3600,
            "user": {
                "username": user["username"],
                "role": user["role"],
                "user_id": user.get("id"),
                "node_id": user.get("node_id")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API login error for {username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )

# ========== UTILITY ROUTES ==========

@router.get("/api/auth/verify", tags=['auth'])
async def verify_token(request: Request):
    """Verify if current token is valid"""
    try:
        # Get token from cookie
        token = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token found"
            )
        
        # Verify token (implement this in your sva module)
        # user_data = sva.verify_access_token(token)
        
        return {
            "valid": True,
            "message": "Token is valid"
            # "user": user_data  # Include user data if needed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@router.get("/api/auth/me", tags=['auth'])
async def get_current_user(request: Request):
    """Get current authenticated user information"""
    try:
        token = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        # Decode token and get user info
        # user_data = sva.verify_access_token(token)
        
        return {
            # "user": user_data,
            "authenticated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication verification failed"
        )
