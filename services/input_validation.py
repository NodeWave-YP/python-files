# Input validation functions
import logging
import re
from typing import Optional
from services.mqtt_client import mqtt_mac_cache
from services.supabase_client import supabase
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """Validate username format and length"""
    if not username or not username.strip():
        return False, "Username is required"
    
    username = username.strip().lower()
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, None

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """Validate password strength"""
    if not password or not password.strip():
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password is too long (max 128 characters)"
    
    # Check for at least one letter and one number
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, None

def get_available_node() -> tuple[Optional[str], Optional[str], Optional[str]]:
    if not mqtt_mac_cache:
        logger.warning("MQTT MAC cache is empty — no node MAC detected.")
        return None, None, "System temporarily unavailable. Please try again shortly."
    
    try:
        # Get the most recent MAC/node_id pair
        mac_address, node_id = list(mqtt_mac_cache.items())[-1]
        logger.info(f"Using node_id {node_id} for registration (MAC: {mac_address})")
        return mac_address, node_id, None
    except Exception as e:
        logger.error(f"Error retrieving node information: {e}")
        return None, None, "Error retrieving node information. Please try again."

async def check_username_exists(username: str) -> bool:
    """Check if username already exists in database"""
    try:
        result = supabase.table("user_accounts").select("username").eq("username", username).limit(1).execute()
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error checking username existence: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
