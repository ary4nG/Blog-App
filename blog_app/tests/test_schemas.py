import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate
from app.schemas.post import PostCreate, PostUpdate
from app.schemas.comment import CommentCreate


# ---- UserCreate ----

def test_valid_user():
    user = UserCreate(username="john", password="password123")
    assert user.username == "john"
    assert user.password == "password123"


def test_username_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="ab", password="password123")


def test_username_too_long():
    with pytest.raises(ValidationError):
        UserCreate(username="a" * 31, password="password123")


def test_password_too_short():
    with pytest.raises(ValidationError):
        UserCreate(username="john", password="short")   # 5 chars, min is 8


# ---- PostCreate ----

def test_valid_post():
    post = PostCreate(title="My Post", body="Some body text")
    assert post.title == "My Post"


def test_post_empty_title():
    with pytest.raises(ValidationError):
        PostCreate(title="", body="Some body")


def test_post_title_too_long():
    with pytest.raises(ValidationError):
        PostCreate(title="a" * 201, body="Some body")


def test_post_empty_body():
    with pytest.raises(ValidationError):
        PostCreate(title="Valid title", body="")


# ---- PostUpdate (partial) ----

def test_post_update_allows_omitting_fields():
    # both fields optional -> constructing with none should be valid
    update = PostUpdate()
    assert update.title is None
    assert update.body is None


def test_post_update_single_field():
    update = PostUpdate(title="New title")
    assert update.title == "New title"
    assert update.body is None


# ---- CommentCreate ----

def test_valid_comment():
    comment = CommentCreate(body="Nice post!")
    assert comment.body == "Nice post!"


def test_comment_empty_body():
    with pytest.raises(ValidationError):
        CommentCreate(body="")


def test_comment_body_too_long():
    with pytest.raises(ValidationError):
        CommentCreate(body="a" * 1001)   # max is 1000
