from pydantic import BaseModel, ConfigDict, Field

class PostCreate(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    body: str = Field(min_length=1,max_length=10000)

class PostUpdate(BaseModel):
    title: None | str = Field(default=None, min_length=1,max_length=200)
    body: None | str = Field(default=None, min_length=1,max_length=10000)

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str 
    body: str 
    author_id: int
