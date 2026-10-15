from pydantic import BaseModel, ConfigDict, Field

class CommentCreate(BaseModel):
    body: str = Field(min_length=1,max_length=1000)

class CommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    body: str 
    post_id: int
    author_id: int