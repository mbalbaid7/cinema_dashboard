import pandas as pd

# تحميل البيانات من ملفات CSV
tickets = pd.read_csv("tickets.csv")
movies = pd.read_csv("movies.csv")
theaters = pd.read_csv("theaters.csv")
shows = pd.read_csv("shows.csv")
customers = pd.read_csv("customers.csv")

# دمج البيانات الأساسية
df = tickets.merge(movies, on="movie_id", how="left") \
            .merge(theaters, on="theater_id", how="left") \
            .merge(shows[["show_id", "start_time"]], on="show_id", how="left") \
            .merge(customers, on="customer_id", how="left")

# معالجة الأعمدة
df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
df["purchase_time"] = pd.to_datetime(df["purchase_time"], errors="coerce")
df["total"] = pd.to_numeric(df["total"], errors="coerce")  # مهم


def get_data():
    """إرجاع نسخة من DataFrame"""
    return df.copy()
