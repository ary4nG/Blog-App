from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.schemas.comment import CommentResponse,CommentCreate
from app.models.user import User
from app.services import comment_service
router = APIRouter(prefix="/posts", tags=["comments"])

@router.post("/{post_id}/comments",response_model=CommentResponse,status_code=201)
async def create_comment(post_id: int,comment_data: CommentCreate, current_user: User=Depends(get_current_user),db :AsyncSession = Depends(get_db)):
    return await comment_service.create_comment(post_id,comment_data,current_user.id,db)


@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    return await comment_service.list_comments(post_id, db)