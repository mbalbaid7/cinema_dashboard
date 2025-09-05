from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cinema_api.routers import movies, customers, revenue, filters
from cinema_api import data_loader

app = FastAPI(title="Cinema API - Modular")

# CORS علشان Streamlit يقدر يتصل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# تسجيل الـ Routers
app.include_router(movies.router)
app.include_router(customers.router)
app.include_router(revenue.router)
app.include_router(filters.router)


@app.get("/")
def root():
    return {"message": "Cinema API is running 🚀"}
