from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Health Check", description="Check the health of the application")
def health_check():
    return {"status": "healthy"}