import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# إعداد الصفحة
st.set_page_config(page_title="لوحة دور السينما", layout="wide")
st.title("🎬 لوحة مؤشرات دور السينما")

API = "https://cinema-dashboard-2.onrender.com"

params = {}
# ===== Fetch filtered data =====
try:
    r = requests.get(f"{API}/filter/data", params=params)
    r.raise_for_status()
    dff = pd.DataFrame(r.json())

    if not dff.empty:

        # ===== Sidebar Filters =====
        st.sidebar.header("🔍 الفلاتر")

        # تحويل العمود إلى تاريخ (احتياطاً)
        dff["purchase_time"] = pd.to_datetime(dff["purchase_time"])

        # نجيب أصغر وأكبر تاريخ من البيانات
        min_date, max_date = dff["purchase_time"].min(
        ), dff["purchase_time"].max()

        # عنصر لاختيار النطاق
        date_range = st.sidebar.date_input(
            "📅 نطاق التاريخ",
            (min_date, max_date)
        )

        # فلترة البيانات حسب النطاق
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start, end = date_range
            dff = dff[(dff["purchase_time"] >= pd.to_datetime(start)) &
                      (dff["purchase_time"] <= pd.to_datetime(end))]
        # 🎬 فلتر الأفلام
        movies = dff[["movie_id", "Title"]].drop_duplicates()
        title_to_id = dict(zip(movies["Title"], movies["movie_id"]))

        sel_titles = st.sidebar.multiselect(
            "🎬 اختر الأفلام",
            options=list(title_to_id.keys())
        )

        # لو فيه أفلام مختارة نصفي البيانات
        if sel_titles:
            sel_movie_ids = [title_to_id[t] for t in sel_titles]
            dff = dff[dff["movie_id"].isin(sel_movie_ids)]

         # فلتر العملاء
        customers = dff[["customer_id", "name_y"]]
        name_to_id = dict(zip(customers["name_y"], customers["customer_id"]))

        sel_customers = st.sidebar.multiselect(
            "👥 العملاء", options=list(name_to_id.keys())
        )

        # لو فيه عملاء مختارة نصفي البيانات
        if sel_customers:
            sel_customers_ids = [name_to_id[c] for c in sel_customers]
            dff = dff[dff["customer_id"].isin(sel_customers_ids)]

         #  🏢 فلتر الصالات

        theaters = dff[["theater_id", "name_x"]].drop_duplicates()
        theater_to_id = dict(zip(theaters["name_x"], theaters["theater_id"]))

        sel_theater = st.sidebar.multiselect(
            "🏢 الصالات", options=list(theater_to_id.keys())
        )

        # لو فيه صالات مختارة نصفي البيانات
        if sel_theater:
            sel_theaters_ids = [theater_to_id[h] for h in sel_theater]
            dff = dff[dff["theater_id"].isin(sel_theaters_ids)]

       # 🎟️ فلتر نوع المقعد
        seat_options = dff["seat_type"].dropna().astype(
            str).str.strip().unique()

        sel_seats = st.sidebar.multiselect(
            "🎟️ نوع المقعد", options=sorted(seat_options)
        )

        # لو فيه مقاعد مختارة نصفي البيانات
        if sel_seats:
            dff = dff[dff["seat_type"].isin(sel_seats)]

        if "total" in dff.columns:
            min_val, max_val = int(dff["total"].min()), int(dff["total"].max())
        if min_val < max_val:
            sales_range = st.sidebar.slider(
                "💰 نطاق المبيعات",
                min_val, max_val, (min_val, max_val)
            )

        # فلترة البيانات
            dff = dff[(dff["total"] >= sales_range[0]) &
                      (dff["total"] <= sales_range[1])]
        else:
            st.sidebar.info(
                "🔹 كل المبيعات لها نفس القيمة تقريبًا، ما في داعي للفلترة.")

        # ===== KPIs =====
        total_sales = float(
            dff["total"].sum()) if "total" in dff.columns else 0.0
        tickets_count = len(dff)
        unique_customers = dff["customer_id"].nunique(
        ) if "customer_id" in dff.columns else 0
        unique_theaters = dff["theater_id"].nunique(
        ) if "theater_id" in dff.columns else 0
        unique_movies = dff["movie_id"].nunique(
        ) if "movie_id" in dff.columns else 0

        # العملاء المتكررين (أكثر من عملية شراء)
        repeat_customers = (
            dff["customer_id"].value_counts().gt(1).sum()
            if "customer_id" in dff.columns else 0
        )
        repeat_ratio = (repeat_customers / unique_customers *
                        100) if unique_customers > 0 else 0

        # تقسيم الأعمدة
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        col1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} SAR")
        col2.metric("🎟️ عدد التذاكر", tickets_count)
        col3.metric("👥 عدد العملاء", unique_customers)
        col4.metric("🏢 عدد الصالات", unique_theaters)
        col5.metric("🎬 عدد الأفلام", unique_movies)
        col6.metric("🔄 العملاء المتكررين",
                    f"{repeat_customers} ({repeat_ratio:.1f}%)",
                    help="عدد العملاء الذين اشتروا أكثر من مرة")

        # Tabs للتحليلات
        tab1, tab2, tab3 = st.tabs(["🎬 الأفلام", "👥 العملاء", "📅 الإيرادات"])
        with tab1:
            # 🎬 Top Movies
            st.subheader("🎬 أفضل 5 أفلام")
            if "Title" in dff.columns and "total" in dff.columns:
                top_movies = (
                    dff.groupby("Title")["total"].sum()
                    .sort_values(ascending=False)
                    .reset_index()
                    .head(5)
                )
            if not top_movies.empty:
                fig = px.bar(
                    top_movies,
                    x="Title",
                    y="total",
                    title="🎬 أفضل 5 أفلام",
                    text_auto=True,
                    color="Title", color_discrete_sequence=px.colors.qualitative.Set2


                )

                st.plotly_chart(fig, use_container_width=True)
                with st.expander("📋 عرض التفاصيل"):
                    st.dataframe(top_movies, use_container_width=True)
            else:
                st.info("لا توجد أفلام مطابقة للفلاتر")

        with tab2:

            # 👥 أفضل العملاء
            st.subheader("👥 أفضل العملاء")
            if "name_y" in dff.columns and "total" in dff.columns:
                top_customers = (
                    dff.groupby("name_y")["total"].sum()
                    .sort_values(ascending=False)
                    .reset_index()
                    .head(5)
                )
                if not top_customers.empty:
                    fig2 = px.pie(top_customers, values="total", names="name_y", color="name_y", color_discrete_sequence=px.colors.qualitative.Set2,
                                  title="👥 أفضل 5 عملاء", hole=0.1)

                    st.plotly_chart(fig2, use_container_width=True)
                    with st.expander("📋 عرض التفاصيل"):
                        st.dataframe(top_customers, use_container_width=True)
            else:
                st.info("لا توجد عملاء مطابقة للفلاتر")
        with tab3:

            # ===== Daily Revenue =====
            st.subheader("📅 الإيرادات اليومية")
            if "purchase_time" in dff.columns and "total" in dff.columns:
                daily_rev = dff.groupby("purchase_time")[
                    "total"].sum().reset_index()
                if not daily_rev.empty:
                    fig3 = px.line(
                        daily_rev,
                        x="purchase_time",
                        y="total",
                        color_discrete_sequence=px.colors.qualitative.Set2,
                        markers=True,
                        title="📅 Daily Revenue"
                    )
                st.plotly_chart(fig3, use_container_width=True)
                with st.expander("📋 عرض التفاصيل"):

                    st.dataframe(daily_rev, use_container_width=True)
            else:
                st.info("لا توجد بيانات مطابقة للفلاتر")

    else:
        st.warning("⚠️ لا توجد بيانات مطابقة للفلاتر الحالية.")

except Exception as e:
    st.error(f"⚠️ خطأ في الاتصال بالـ API: {e}")
    dff = pd.DataFrame()
