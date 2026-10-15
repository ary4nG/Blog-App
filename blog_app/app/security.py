from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from app.config import settings
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_pwd: str)->bool:
    return pwd_context.verify(password, hashed_pwd)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm= settings.ALGORITHM)
    return encoded_token

def decode_access_token(token: str):
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms= [settings.ALGORITHM])
    return payload