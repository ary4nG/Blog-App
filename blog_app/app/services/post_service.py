from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Post, User
from app.schemas.post import PostCreate, PostUpdate
from app.exceptions import PostNotFoundError, ForbiddenError
from app.logger import get_logger
from app.events import producer

logger = get_logger(__name__)


async def create_post(post_data: PostCreate, author_id: int, db: AsyncSession) -> Post:
    new_post = Post(
        title=post_data.title,
        body=post_data.body,
        author_id=author_id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    logger.info("post_created", post_id=new_post.id, author_id=author_id)
    await producer.publish({
        "event": "post_created",
        "post_id": new_post.id,
        "title": new_post.title,
        "author_id": author_id,
    })
    return new_post


async def list_posts(db: AsyncSession) -> list[Post]:
    result = await db.execute(select(Post).order_by(Post.id.desc()))
    return result.scalars().all()


async def get_post_or_404(post_id: int, db: AsyncSession) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise PostNotFoundError(post_id)
    return post


async def update_post(post_id: int, post_data: PostUpdate, current_user: User, db: AsyncSession) -> Post:
    post = await get_post_or_404(post_id, db)
    if post.author_id != current_user.id and current_user.role.value != "admin":
        logger.warning("post_permission_denied", post_id=post_id, user_id=current_user.id)
        raise ForbiddenError()

    for field, value in post_data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    logger.info("post_updated", post_id=post_id, user_id=current_user.id)
    return post


async def delete_post(post_id: int, current_user: User, db: AsyncSession) -> None:
    post = await get_post_or_404(post_id, db)
    if post.author_id != current_user.id and current_user.role.value != "admin":
        logger.warning("post_permission_denied", post_id=post_id, user_id=current_user.id)
        raise ForbiddenError()

    await db.delete(post)
    await db.commit()
    logger.info("post_deleted", post_id=post_id, user_id=current_user.id)
