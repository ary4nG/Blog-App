from app.schemas.comment import CommentCreate
from app.services.post_service import get_post_or_404
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment
from sqlalchemy import select
from app.logger import get_logger
from app.events import producer

logger = get_logger(__name__)


async def create_comment(post_id:int, comment_data:CommentCreate, author_id:int, db:AsyncSession):
    await get_post_or_404(post_id,db)
    new_comment = Comment(body=comment_data.body,author_id=author_id,post_id=post_id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    logger.info("comment_created", comment_id=new_comment.id, post_id=post_id, author_id=author_id)
    # publish AFTER commit — only emit events for things that actually persisted
    await producer.publish({
        "event": "comment_created",
        "comment_id": new_comment.id,
        "post_id": post_id,
        "author_id": author_id,
    })
    return new_comment

async def list_comments(post_id:int, db: AsyncSession)->list[Comment]:
    result = await db.execute(select(Comment).where(Comment.post_id==post_id))
    comments = result.scalars().all()
    return comments