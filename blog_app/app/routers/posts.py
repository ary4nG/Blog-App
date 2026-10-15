from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import User
from app.schemas.post import PostCreate, PostUpdate, PostResponse
from app.services import post_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(require_role("author", "admin")),
    db: AsyncSession = Depends(get_db),
):
    return await post_service.create_post(post_data, current_user.id, db)


@router.get("", response_model=list[PostResponse])
async def list_posts(db: AsyncSession = Depends(get_db)):
    return await post_service.list_posts(db)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    return await post_service.get_post_or_404(post_id, db)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await post_service.update_post(post_id, post_data, current_user, db)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await post_service.delete_post(post_id, current_user, db)
