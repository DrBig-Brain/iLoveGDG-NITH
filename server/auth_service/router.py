from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from .auth_manager import create_api_key, validate_api_key, revoke_api_key, list_api_keys

router = APIRouter(prefix="/auth", tags=["Authentication"])


class CreateKeyRequest(BaseModel):
    client_name: str = Field(..., description="Name or identifier of the client application")
    tier: str = Field("standard", description="Pricing/access tier: free, standard, or enterprise")


class RevokeKeyRequest(BaseModel):
    api_key: str = Field(..., description="API key to revoke")


class ValidateKeyRequest(BaseModel):
    api_key: str = Field(..., description="API key to validate")


@router.post("/keys")
def generate_key(req: CreateKeyRequest):
    """Generate a new API key for a client application."""
    new_key = create_api_key(client_name=req.client_name, tier=req.tier)
    return {
        "status": "success",
        "message": "API key generated successfully",
        "key_data": new_key,
    }


@router.get("/keys")
def get_all_keys():
    """List all API keys (masked for security)."""
    keys = list_api_keys()
    return {"status": "success", "keys": keys}


@router.post("/validate")
def verify_key(req: ValidateKeyRequest):
    """Validate an API key."""
    client = validate_api_key(req.api_key)
    if not client:
        raise HTTPException(status_code=401, detail="Invalid, inactive, or revoked API key")
    return {
        "status": "success",
        "valid": True,
        "client": client,
    }


@router.post("/revoke")
def revoke_key_endpoint(req: RevokeKeyRequest):
    """Revoke an existing API key."""
    success = revoke_api_key(req.api_key)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {
        "status": "success",
        "message": "API key has been revoked",
    }


def verify_api_key_header(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Dict[str, Any]:
    """Dependency helper to verify API key from header."""
    key = None
    if x_api_key:
        key = x_api_key
    elif authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            key = parts[1]
        else:
            key = authorization

    if not key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide via 'X-API-Key' or 'Authorization: Bearer <key>' header.",
        )

    client = validate_api_key(key)
    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid or revoked API key.",
        )
    return client
