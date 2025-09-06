from pathlib import Path
import pandas as pd

# تحديد مسار المجلد الحالي (cinema_api)
BASE_DIR = Path(__file__).resolve().parent

# تحميل البيانات من الملفات
tickets = pd.read_csv(BASE_DIR / "tickets.csv")
movies = pd.read_csv(BASE_DIR / "movies.csv")
theaters = pd.read_csv(BASE_DIR / "theaters.csv")
shows = pd.read_csv(BASE_DIR / "shows.csv")
customers = pd.read_csv(BASE_DIR / "customers.csv")

# دمج البيانات الأساسية (tickets + movies + theaters + shows + customers)
df = tickets.merge(movies, on="movie_id", how="left") \
            .merge(theaters, on="theater_id", how="left") \
            .merge(shows[["show_id", "start_time"]], on="show_id", how="left") \
            .merge(customers, on="customer_id", how="left")

# تحويل الأعمدة الزمنية
df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
df["purchase_time"] = pd.to_datetime(df["purchase_time"], errors="coerce")

def get_data():
    return df.copy()
