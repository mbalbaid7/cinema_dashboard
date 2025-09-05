# app_streamlit.py
import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px
from datetime import datetime

API = "http://127.0.0.1:8000"  # عدّليه لو الـ API شغّال على عنوان آخر

st.set_page_config(page_title="🎬 لوحة دور السينما (API)", layout="wide")
st.title("🔗 لوحة دور السينما (API) — Streamlit")
# -----------------------
# 1) تحميل بيانات خام (cache)
# -----------------------


@st.cache_data(ttl=60)
def load_raw():
    """نحاول جلب بيانات 'خام' من API عبر /filter/data بدون بارامترات
       (الـ API المفروض ترجع أول N صفوف حسب إعدادها)."""
    try:
        r = requests.get(f"{API}/filter/data", timeout=10)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        # تحويل الأنواع الأساسية إذا وجدت
        if "purchase_time" in df.columns:
            df["purchase_time"] = pd.to_datetime(
                df["purchase_time"], errors="coerce")
        if "total" in df.columns:
            df["total"] = pd.to_numeric(df["total"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"خطأ عند تحميل البيانات من الـ API: {e}")
        return pd.DataFrame()


df_raw = load_raw()
if df_raw.empty:
    st.warning(
        "لم يتم تحميل بيانات أولية من الـ API أو البيانات فارغة — تأكدي أن `/filter/data` شغال.")
    st.stop()

# -----------------------
# 2) Sidebar: فلاتر (date, movies, customers, theaters, seat_type, min_total)
# -----------------------
st.sidebar.header("🔍 الفلاتر")

# تاريخ (نستخدم نطاق حسب data)
min_date = df_raw["purchase_time"].min().date(
) if "purchase_time" in df_raw.columns else datetime.today().date()
max_date = df_raw["purchase_time"].max().date(
) if "purchase_time" in df_raw.columns else datetime.today().date()
date_range = st.sidebar.date_input("📅 نطاق التاريخ", (min_date, max_date))

# دوال مساعدة لاستخراج الأسماء/أعمدة مع fallback


def col_pair(df, id_candidates, name_candidates):
    """ترجع (id_col, name_col) إن وُجدا، أو (None,None)."""
    id_col = next((c for c in id_candidates if c in df.columns), None)
    name_col = next((c for c in name_candidates if c in df.columns), None)
    return id_col, name_col


movie_id_col, movie_name_col = col_pair(
    df_raw, ["movie_id", "movieId", "movie"], ["Title", "title", "movie_title"])
cust_id_col, cust_name_col = col_pair(df_raw, ["customer_id", "cust_id"], [
                                      "Customer", "name", "customer_name", "name_y"])
theater_id_col, theater_name_col = col_pair(
    df_raw, ["theater_id"], ["name_x", "theater_name", "name"])
seat_col = next(
    (c for c in ["seat_type", "seat", "seatType"] if c in df_raw.columns), None)

# خيارات الأفلام (عرض الاسم لكن نرسل الـ id)
movie_options = []
movie_map = {}
if movie_id_col and movie_name_col:
    movies_df = df_raw[[movie_id_col, movie_name_col]
                       ].drop_duplicates().dropna()
    movie_map = dict(zip(movies_df[movie_name_col].astype(
        str), movies_df[movie_id_col].astype(str)))
    movie_options = sorted(movie_map.keys())
elif movie_id_col:
    movie_options = sorted(df_raw[movie_id_col].astype(
        str).drop_duplicates().tolist())

sel_movies = st.sidebar.multiselect("🎬 الأفلام", options=movie_options)

# عملاء
cust_options = []
cust_map = {}
if cust_id_col and cust_name_col:
    cust_df = df_raw[[cust_id_col, cust_name_col]].drop_duplicates().dropna()
    cust_map = dict(zip(cust_df[cust_name_col].astype(
        str), cust_df[cust_id_col].astype(str)))
    cust_options = sorted(cust_map.keys())
elif cust_id_col:
    cust_options = sorted(df_raw[cust_id_col].astype(
        str).drop_duplicates().tolist())

sel_customers = st.sidebar.multiselect("👥 العملاء", options=cust_options)

# صالات
theater_options = []
theater_map = {}
if theater_id_col and theater_name_col:
    th_df = df_raw[[theater_id_col, theater_name_col]
                   ].drop_duplicates().dropna()
    theater_map = dict(zip(th_df[theater_name_col].astype(
        str), th_df[theater_id_col].astype(str)))
    theater_options = sorted(theater_map.keys())
elif theater_id_col:
    theater_options = sorted(df_raw[theater_id_col].astype(
        str).drop_duplicates().tolist())

sel_theaters = st.sidebar.multiselect("🏢 الصالات", options=theater_options)

# نوع المقعد
seat_options = df_raw[seat_col].dropna().astype(
    str).unique().tolist() if seat_col else []
sel_seats = st.sidebar.multiselect(
    "💺 نوع المقعد", options=sorted(seat_options))

# الحد الأدنى للمبيعات
# min_total = st.sidebar.number_input(
#     "💰 الحد الأدنى للمبيعات (>=)", min_value=0.0, value=0.0, step=10.0)
# نحدد الحد الأدنى
min_total = st.slider("💰 اختر الحد الأدنى للمبيعات", 0, 200, 0)
# زر تنفيذ الفلتر
if st.sidebar.button("تطبيق الفلاتر"):
    # -----------------------
    # 3) تحويل اختيارات المستخدم إلى بارامترات للـ API (نرسل الـ IDs)
    # -----------------------
    params = {}
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        params["start_date"] = str(date_range[0])
        params["end_date"] = str(date_range[1])

    if sel_movies:
        # نحول الأسماء إلى IDs إذا كان لدينا map، وإلا نرسل الأسماء/IDs مباشرة
        if movie_map:
            movie_ids = [movie_map[m] for m in sel_movies]
        else:
            movie_ids = sel_movies
        params["movies"] = ",".join(movie_ids)

    if sel_customers:
        if cust_map:
            customer_ids = [cust_map[c] for c in sel_customers]
        else:
            customer_ids = sel_customers
        params["customers"] = ",".join(customer_ids)

    if sel_theaters:
        if theater_map:
            th_ids = [theater_map[t] for t in sel_theaters]
        else:
            th_ids = sel_theaters
        params["theaters"] = ",".join(th_ids)

    if sel_seats:
        params["seat_type"] = ",".join(sel_seats)

    if min_total and min_total > 0:
        params["min_total"] = str(min_total)

    # -----------------------
    # 4) طلب البيانات المفلترة من الـ API
    # -----------------------
    try:
        r = requests.get(f"{API}/filter/data", params=params, timeout=15)
        r.raise_for_status()
        dff = pd.DataFrame(r.json())
        if not dff.empty:
            if "purchase_time" in dff.columns:
                dff["purchase_time"] = pd.to_datetime(
                    dff["purchase_time"], errors="coerce")
            if "total" in dff.columns:
                dff["total"] = pd.to_numeric(dff["total"], errors="coerce")
        else:
            st.warning("لا توجد بيانات مطابقة للفلاتر الحالية.")
    except Exception as e:
        st.error(f"خطأ في الاتصال بالـ API: {e}")
        st.stop()

    # -----------------------
    # 5) عرض النتائج + KPIs + رسومات + تحميل Excel
    # -----------------------
    st.success(f"✅ عدد السجلات بعد التصفية: {len(dff)}")
    st.dataframe(dff.head(20), use_container_width=True)

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    total_sales = float(dff["total"].sum()) if "total" in dff.columns else 0.0
    tickets_count = len(dff)
    unique_customers = dff["customer_id"].nunique(
    ) if "customer_id" in dff.columns else 0
    unique_movies = dff["movie_id"].nunique(
    ) if "movie_id" in dff.columns else 0

    col1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} SAR")
    col2.metric("🎟️ عدد التذاكر", f"{tickets_count:,}")
    col3.metric("👥 العملاء الفريدون", f"{unique_customers}")
    col4.metric("🎬 الأفلام الفريدة", f"{unique_movies}")

    # Top Movies (محليًا بعد الفلترة)
    if "Title" in dff.columns and "total" in dff.columns:
        top_movies = dff.groupby("Title")["total"].sum().sort_values(
            ascending=False).head(10).reset_index()
        fig = px.bar(top_movies, x="Title", y="total",
                     title="🏷️ الإيرادات حسب الفيلم (بعد الفلترة)", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)

     # Revenue by Theater
    if theater_name_col and "total" in dff.columns:
        rev_th = dff.groupby(theater_name_col)["total"].sum(
        ).sort_values(ascending=False).reset_index()
        fig2 = px.bar(rev_th, x=theater_name_col, y="total",
                      title="🏛️ الإيرادات حسب الصالة", text_auto=True)
        st.plotly_chart(fig2, use_container_width=True)

    # Daily revenue
    if "purchase_time" in dff.columns and "total" in dff.columns:
        daily = dff.groupby(dff["purchase_time"].dt.date)[
            "total"].sum().reset_index()
        daily.columns = ["date", "total"]
        daily["date"] = pd.to_datetime(daily["date"])
        fig3 = px.line(daily, x="date", y="total", markers=True,
                       title="📅 الإيرادات اليومية")
        st.plotly_chart(fig3, use_container_width=True)

     # هيستوغرام لتوزيع المبيعات
    # fig = px.histogram(
    #     dff, x="total", nbins=20,
    #     title=f"📊 توزيع المبيعات (مع حد أدنى {min_total})"
    # )
    # st.plotly_chart(fig, use_container_width=True)

    # # عرض القيم الدنيا والعظمى
    # st.write("Min total:", dff["total"].min())
    # st.write("Max total:", dff["total"].max())

    st.title("🎟️ مقارنة توزيع المبيعات")

# ===== جلب البيانات الكاملة (بدون فلترة) =====
    # نحدد limit كبير شوية
    r_full = requests.get(f"{API}/filter/data?limit=5000")
    r_full.raise_for_status()
    df_full = pd.DataFrame(r_full.json())

    # ===== اختيار الحد الأدنى =====
    min_total = st.slider("💰 اختر الحد الأدنى للمبيعات", 0,
                          int(df_full["total"].max()), 0)

    # ===== جلب البيانات المفلترة =====
    params = {"min_total": min_total}
    r_filtered = requests.get(f"{API}/filter/data", params=params)
    r_filtered.raise_for_status()
    df_filtered = pd.DataFrame(r_filtered.json())

    # ===== رسم المقارنة =====
    if df_filtered.empty:
        st.warning("⚠️ لا توجد بيانات مطابقة.")
    else:
        st.success(f"✅ عدد السجلات بعد الفلترة: {len(df_filtered)}")

        # إضافة عمود لتحديد الحالة
        df_full["status"] = "📊 قبل الفلترة"
        df_filtered["status"] = f"✅ بعد الفلترة (>{min_total})"

        # دمج الاثنين
        combined = pd.concat([df_full, df_filtered])

        fig = px.histogram(
            combined, x="total", nbins=20, color="status",
            barmode="overlay",  # overlay = فوق بعض للوضوح
            title=f"📊 مقارنة توزيع المبيعات (حد أدنى {min_total})"
        )
        st.plotly_chart(fig, use_container_width=True)

        # إظهار القيم
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Min (قبل)", f"{df_full['total'].min():,.2f}")
            st.metric("Max (قبل)", f"{df_full['total'].max():,.2f}")
        with col2:
            st.metric("Min (بعد)", f"{df_filtered['total'].min():,.2f}")
            st.metric("Max (بعد)", f"{df_filtered['total'].max():,.2f}")

    # Excel export
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dff.to_excel(writer, index=False, sheet_name="Filtered")
    buffer.seek(0)
    st.download_button("📥 تحميل Excel (البيانات بعد الفلترة)", data=buffer, file_name="filtered_data.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("اضغطي 'تطبيق الفلاتر' في الشريط الجانبي لعرض النتائج.")
