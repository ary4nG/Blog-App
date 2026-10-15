from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.schemas.user import UserCreate
from app.security import hash_password, verify_password, create_access_token
from app.exceptions import UsernameTakenError, InvalidCredentialsError
from app.logger import get_logger

logger = get_logger(__name__)


async def register_user(user_data: UserCreate, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        logger.warning("registration_failed", username=user_data.username, reason="username_taken")
        raise UsernameTakenError(user_data.username)

    new_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logger.info("user_registered", username=new_user.username, user_id=new_user.id)
    return new_user


async def login_user(username: str, password: str, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        logger.warning("login_failed", username=username, reason="invalid_credentials")
        raise InvalidCredentialsError()

    token = create_access_token({"sub": user.username, "role": user.role.value})
    logger.info("login_success", username=user.username, role=user.role.value)
    return {"access_token": token, "token_type": "bearer"}