"""
Security Module - Authentication & Authorization
Handles JWT tokens, password hashing, role-based access
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.constants import ROLES, ROLE_PERMISSIONS


# ========== PASSWORD HASHING ==========
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    Uses configurable rounds from settings
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    Constant-time comparison prevents timing attacks
    """
    return pwd_context.verify(plain_password, hashed_password)


# ========== JWT TOKEN GENERATION ==========
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload to encode (typically user_id, username, role)
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token
    Longer expiration, used to get new access tokens
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ========== AUTHENTICATION DEPENDENCY ==========
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user
    Validates JWT token from Authorization header
    
    Usage in routes:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Extract user info
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return {
        "user_id": user_id,
        "username": payload.get("username"),
        "role": payload.get("role", ROLES["viewer"]),
        "email": payload.get("email")
    }


# ========== ROLE-BASED ACCESS CONTROL ==========
def require_role(required_roles: list):
    """
    Dependency factory for role-based access
    
    Usage:
        @router.delete("/events/{event_id}")
        async def delete_event(
            event_id: str,
            user: dict = Depends(require_role(["ADMIN", "OPERATOR"]))
        ):
            ...
    """
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role", ROLES["viewer"])
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )
        
        return user
    
    return role_checker


def require_permission(required_permission: str):
    """
    Check if user has specific permission
    
    Usage:
        @router.post("/system/configure")
        async def configure(user: dict = Depends(require_permission("configure"))):
            ...
    """
    async def permission_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role", ROLES["viewer"])
        permissions = ROLE_PERMISSIONS.get(user_role, [])
        
        if required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {required_permission}"
            )
        
        return user
    
    return permission_checker


# ========== DEMO USER AUTHENTICATION ==========
# For hackathon/demo purposes - Replace with real DB lookup in production
DEMO_USERS = {
    "admin": {
        "user_id": "U001",
        "username": "admin",
        "email": "admin@surveillance.com",
        "hashed_password": hash_password("admin123"),
        "role": ROLES["admin"],
        "active": True
    },
    "operator": {
        "user_id": "U002",
        "username": "operator",
        "email": "operator@surveillance.com",
        "hashed_password": hash_password("operator123"),
        "role": ROLES["operator"],
        "active": True
    },
    "viewer": {
        "user_id": "U003",
        "username": "viewer",
        "email": "viewer@surveillance.com",
        "hashed_password": hash_password("viewer123"),
        "role": ROLES["viewer"],
        "active": True
    }
}


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with username/password
    
    Returns:
        User dict if valid, None otherwise
    """
    user = DEMO_USERS.get(username)
    
    if not user:
        return None
    
    if not user.get("active", False):
        return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    # Don't return hashed password
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    }


# ========== API KEY SUPPORT (Optional) ==========
def verify_api_key(api_key: str) -> bool:
    """
    Verify API key for service-to-service communication
    Useful for camera systems sending events
    """
    # In production, store these in database with rate limits
    VALID_API_KEYS = {
        "CAM_API_KEY_123": {"service": "camera_network", "active": True},
        "ANALYTICS_KEY_456": {"service": "analytics_engine", "active": True}
    }
    
    key_data = VALID_API_KEYS.get(api_key)
    return key_data is not None and key_data.get("active", False)


async def get_api_key_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Alternative auth for API keys
    """
    api_key = credentials.credentials
    
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return {
        "user_id": "SERVICE",
        "username": "api_service",
        "role": ROLES["operator"]  # Service accounts get operator role
    }
