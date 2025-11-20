"""
Production-ready security module for Healthcare AI Pre-authorization API.

Implements authentication, authorization, input validation, and security middleware
for production deployment.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Callable
import os

from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import jwt
from loguru import logger
import re


# Security configuration
class SecurityConfig:
    """Production security configuration."""
    
    # JWT Settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    
    # API Key Settings
    API_KEY_HEADER = "X-API-Key"
    API_KEY_LENGTH = 32
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour
    
    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
    }
    
    # Trusted hosts
    TRUSTED_HOSTS = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,api.healthcare-preauth.ai").split(",")
    
    # Input validation patterns
    PATIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,50}$")
    FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,255}$")
    

# Authentication Classes
security_config = SecurityConfig()
security_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name=security_config.API_KEY_HEADER, auto_error=False)


class APIKeyManager:
    """Manages API key generation, validation, and storage."""
    
    def __init__(self):
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from environment or storage."""
        # In production, load from secure storage (database, secrets manager)
        master_key = os.getenv("HEALTHCARE_PREAUTH_MASTER_API_KEY")
        if master_key:
            self.api_keys[master_key] = {
                "name": "master",
                "created_at": datetime.now(timezone.utc),
                "permissions": ["read", "write", "admin"],
                "rate_limit": 1000,
                "active": True
            }
        
        # Demo/development keys
        demo_key = os.getenv("HEALTHCARE_PREAUTH_DEMO_API_KEY", "demo_key_12345_change_in_production")
        self.api_keys[demo_key] = {
            "name": "demo",
            "created_at": datetime.now(timezone.utc),
            "permissions": ["read"],
            "rate_limit": 100,
            "active": True
        }
    
    def generate_api_key(self, name: str, permissions: List[str] = None) -> str:
        """Generate a new API key."""
        api_key = secrets.token_urlsafe(security_config.API_KEY_LENGTH)
        self.api_keys[api_key] = {
            "name": name,
            "created_at": datetime.now(timezone.utc),
            "permissions": permissions or ["read"],
            "rate_limit": security_config.RATE_LIMIT_REQUESTS,
            "active": True
        }
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return key info."""
        if not api_key:
            return None
        
        key_info = self.api_keys.get(api_key)
        if not key_info or not key_info.get("active"):
            return None
        
        return key_info
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key]["active"] = False
            return True
        return False


class JWTManager:
    """Manages JWT token generation and validation."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(hours=security_config.JWT_EXPIRY_HOURS)
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            security_config.JWT_SECRET_KEY, 
            algorithm=security_config.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, 
                security_config.JWT_SECRET_KEY, 
                algorithms=[security_config.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"JWT validation error: {e}")
            return None


# Global instances
api_key_manager = APIKeyManager()
jwt_manager = JWTManager()


# Authentication Dependencies
async def get_api_key_auth(api_key: Optional[str] = Depends(api_key_header)) -> Dict[str, Any]:
    """Dependency for API key authentication."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    key_info = api_key_manager.validate_api_key(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return key_info


async def get_jwt_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    """Dependency for JWT authentication."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token_data = jwt_manager.verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token_data


async def get_optional_auth(
    api_key: Optional[str] = Depends(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Optional[Dict[str, Any]]:
    """Optional authentication - try API key first, then JWT."""
    try:
        if api_key:
            return await get_api_key_auth(api_key)
    except HTTPException:
        pass
    
    try:
        if credentials:
            return await get_jwt_auth(credentials)
    except HTTPException:
        pass
    
    return None


def require_permissions(required_permissions: List[str]) -> Callable:
    """Decorator to require specific permissions."""
    def permission_dependency(auth_data: Dict[str, Any] = Depends(get_api_key_auth)) -> Dict[str, Any]:
        user_permissions = auth_data.get("permissions", [])
        
        # Check if user has required permissions
        if not any(perm in user_permissions for perm in required_permissions) and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permissions}"
            )
        
        return auth_data
    
    return permission_dependency


# Input Validation
class InputValidator:
    """Input validation and sanitization utilities."""
    
    @staticmethod
    def validate_patient_id(patient_id: str) -> str:
        """Validate patient ID format."""
        if not patient_id or not security_config.PATIENT_ID_PATTERN.match(patient_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid patient ID format. Use alphanumeric characters, hyphens, and underscores only."
            )
        return patient_id.strip()
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate filename format."""
        if not filename or not security_config.FILENAME_PATTERN.match(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename format."
            )
        
        # Prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: directory traversal not allowed."
            )
        
        return filename.strip()
    
    @staticmethod
    def validate_cost_limit(cost_limit: float) -> float:
        """Validate cost limit parameter."""
        if cost_limit < 0 or cost_limit > 10.0:  # Reasonable upper bound
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cost limit must be between 0 and 10.0 USD."
            )
        return cost_limit
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input."""
        if not input_str:
            return ""
        
        # Remove null bytes and control characters
        sanitized = input_str.replace('\0', '').strip()
        
        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized


# Middleware Classes
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        for header, value in security_config.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with IP-based tracking."""
    
    def __init__(self, app, requests_per_window: int = None, window_seconds: int = None):
        super().__init__(app)
        self.requests_per_window = requests_per_window or security_config.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or security_config.RATE_LIMIT_WINDOW
        self.rate_limit_store: Dict[str, List[float]] = {}
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address."""
        # Check for forwarded headers in production
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_requests: List[float], current_time: float) -> List[float]:
        """Remove requests outside the current window."""
        cutoff_time = current_time - self.window_seconds
        return [req_time for req_time in client_requests if req_time > cutoff_time]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/api/health", "/api/health/detailed"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Get and clean old requests for this client
        if client_ip not in self.rate_limit_store:
            self.rate_limit_store[client_ip] = []
        
        client_requests = self.rate_limit_store[client_ip]
        client_requests = self._clean_old_requests(client_requests, current_time)
        
        # Check rate limit
        if len(client_requests) >= self.requests_per_window:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content='{"detail": "Rate limit exceeded. Try again later."}',
                status_code=429,
                headers={"Content-Type": "application/json", "Retry-After": str(self.window_seconds)}
            )
        
        # Add current request
        client_requests.append(current_time)
        self.rate_limit_store[client_ip] = client_requests
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_window - len(client_requests))
        reset_time = int(current_time + self.window_seconds)
        
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} for {request.method} {request.url.path} "
            f"({duration:.3f}s) from {client_ip}"
        )
        
        # Add timing header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response


# Security utilities
def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, expected_token: str) -> bool:
    """Verify CSRF token using constant-time comparison."""
    return hmac.compare_digest(token, expected_token)


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt."""
    if salt is None:
        salt = secrets.token_hex(32)
    
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return password_hash.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify password against hash."""
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(password_hash, computed_hash)


# Production security configuration
def configure_app_security(app):
    """Configure FastAPI app with production security settings."""
    
    # Add security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=security_config.TRUSTED_HOSTS
    )
    
    logger.info("Production security middleware configured")
    return app