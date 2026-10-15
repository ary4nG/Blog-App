from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from enum import Enum
from app.database import Base

if TYPE_CHECKING:
    from app.models.post import Post
    from app.models.comment import Comment

class UserRole(str,Enum):
    ADMIN = "admin"
    AUTHOR = "author"
    READER = "reader"
 

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True,index=True)
    hashed_password: Mapped[str]
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole),default=UserRole.AUTHOR)
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        passive_deletes=True
    )

    comments: Mapped[list["Comment"]] = relationship(
        back_populates="author",
        passive_deletes=True
    )

 

