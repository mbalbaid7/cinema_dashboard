from fastapi import APIRouter
from cinema_api.data_loader import get_data



router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/top")
def top_customers(limit: int = 5):
    df = get_data()
    top = df.groupby("customer_id")["total"].sum(
    ).sort_values(ascending=False).head(limit)
    return top.to_dict()
