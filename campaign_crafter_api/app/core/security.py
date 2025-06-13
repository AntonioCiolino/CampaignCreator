from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken
from campaign_crafter_api.app.core.config import settings
import base64
import hashlib

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Fernet key generation and instance
def _get_fernet_key() -> bytes:
    """
    Derives a Fernet-compatible key from settings.SECRET_KEY.
    Hashes SECRET_KEY using SHA256 and then encodes it to URL-safe base64.
    Fernet keys must be 32 bytes and URL-safe base64 encoded.
    """
    hashed_secret = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(hashed_secret)

fernet = Fernet(_get_fernet_key())

def encrypt_key(plain_text_key: str) -> str:
    """Encrypts a plain text key using Fernet."""
    if not plain_text_key:
        return ""
    encrypted_bytes = fernet.encrypt(plain_text_key.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')

def decrypt_key(encrypted_key: str) -> str:
    """
    Decrypts an encrypted key using Fernet.
    Returns an empty string if decryption fails.
    """
    if not encrypted_key:
        return ""
    try:
        decrypted_bytes = fernet.decrypt(encrypted_key.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except InvalidToken:
        # Log this event in a real application
        # print(f"Decryption failed for token: {encrypted_key[:20]}...") # Be careful with logging sensitive data
        return ""
    except Exception: # Catch any other Fernet related exceptions
        # print(f"An unexpected error occurred during decryption of token: {encrypted_key[:20]}...")
        return ""

# Password Hashing (keeping it here for now, or can be in crud.py as it is)
# If moving from crud.py, ensure crud.py imports them from here.
# For this task, we assume they are in crud.py and will be used from there if needed by auth_service.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)
# def get_password_hash(password: str) -> str:
#     return pwd_context.hash(password)

# JWT Token Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
