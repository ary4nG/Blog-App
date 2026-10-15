from fastapi import APIRouter
from app.events.consumer import _activity

router = APIRouter()

@router.get("/activity")
async def get_activity():
    return list(reversed(_activity))

