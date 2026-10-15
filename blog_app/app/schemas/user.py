from pydantic import BaseModel, ConfigDict, Field
from app.models.user import UserRole

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=100)

 

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str