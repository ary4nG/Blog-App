from app.database import AsyncSessionLocal
from jose import jwt,JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models import User
from app.exceptions import InvalidTokenError, ForbiddenError
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme),db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise InvalidTokenError()
    except JWTError:
        raise InvalidTokenError()
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalar_one_or_none()
    if user is None:
        raise InvalidTokenError()
    return user


def require_role(*allowed):
    async def checker(user: User = Depends(get_current_user)):
        if user.role.value not in allowed:
            raise ForbiddenError()
        return user
    return checker
