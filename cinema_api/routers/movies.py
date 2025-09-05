from fastapi import APIRouter
from cinema_api.data_loader import get_data


router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/top")
def top_movies(limit: int = 5):
    df = get_data()
    top = df.groupby("Title")["total"].sum().sort_values(
        ascending=False).head(limit)
    return top.to_dict()
