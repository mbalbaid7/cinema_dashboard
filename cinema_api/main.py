from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# استدعاء الراوترات من الباكيج
from cinema_api.routers import movies, customers, revenue, filters

app = FastAPI(title="Cinema API")

# تفعيل CORS عشان Streamlit يتصل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تسجيل الـ Routers
app.include_router(movies.router, prefix="/movies", tags=["Movies"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(revenue.router, prefix="/revenue", tags=["Revenue"])
app.include_router(filters.router, prefix="/filter", tags=["Filters"])


@app.get("/")
def root():
    return {"message": "Cinema API is running 🚀"}
