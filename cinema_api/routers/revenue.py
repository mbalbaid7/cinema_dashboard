from fastapi import APIRouter
from data_loader import get_data


router = APIRouter(prefix="/revenue", tags=["Revenue"])


@router.get("/daily")
def daily_revenue():
    df = get_data()
    daily = df.groupby(df["purchase_time"].dt.date)[
        "total"].sum().reset_index()
    return dict(zip(daily["purchase_time"].astype(str), daily["total"]))
