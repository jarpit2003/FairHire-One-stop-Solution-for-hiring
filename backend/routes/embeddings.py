from fastapi import APIRouter

router = APIRouter()


@router.post("/embed")
async def embed():
    return {"message": "not implemented"}
