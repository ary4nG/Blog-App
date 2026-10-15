from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from enum import Enum
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.post import Post

class Comment(Base):

    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    author: Mapped["User"] = relationship(back_populates="comments")
    post: Mapped["Post"] = relationship(back_populates="comments")