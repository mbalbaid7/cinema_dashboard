from fastapi import APIRouter, Query
import pandas as pd
from data_loader import get_data


router = APIRouter(prefix="/filter", tags=["Filters"])


@router.get("/data")
def filter_data(
    start_date: str = None,
    end_date: str = None,
    customers: str = Query(None),
    movies: str = Query(None),
    theaters: str = Query(None),
    seat_type: str = Query(None),
    min_total: float = Query(None),
):
    df = get_data()

    if start_date:
        df = df[df["purchase_time"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["purchase_time"] <= pd.to_datetime(end_date)]

    if customers:
        cust_list = [c.strip().lower() for c in customers.split(",")]
        df = df[df["customer_id"].str.lower().isin(cust_list)]

    if movies:
        mov_list = [m.strip().lower() for m in movies.split(",")]
        df = df[df["movie_id"].str.lower().isin(mov_list)]

    if theaters:
        th_list = [t.strip().lower() for t in theaters.split(",")]
        df = df[df["theater_id"].str.lower().isin(th_list)]

    if seat_type:
        seat_list = [s.strip().lower() for s in seat_type.split(",")]
        df = df[df["seat_type"].str.lower().isin(seat_list)]

    if min_total is not None:
        df = df[df["total"] >= float(min_total)]

    return df.head(100).to_dict(orient="records")
