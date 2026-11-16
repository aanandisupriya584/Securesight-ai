import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .database import get_db
from .models import OrganizationMember, User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)

def secret() -> str:
    value = os.getenv("JWT_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("JWT_SECRET must be configured with at least 32 characters")
    return value

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def make_token(user: User) -> str:
    expiry = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    return jwt.encode({"sub": user.id, "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry)}, secret(), algorithm="HS256")

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, secret(), algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user

def current_membership(user: User = Depends(current_user), db: Session = Depends(get_db)) -> OrganizationMember:
    membership = db.query(OrganizationMember).filter_by(user_id=user.id).order_by(OrganizationMember.id).first()
    if membership is None:
        raise HTTPException(status_code=403, detail="No organization membership")
    return membership
