import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ===== إعداد الصفحة =====
st.set_page_config(page_title="لوحة دور السينما", layout="wide")

API = "https://cinema-dashboard-2.onrender.com"  # رابط الـ API بعد النشر

# ===== حالة تسجيل الدخول =====
if "user" not in st.session_state:
    st.session_state.user = None

# ===== واجهة تسجيل الدخول =====
if st.session_state.user is None:
    st.title("🔐 تسجيل الدخول")

    username = st.text_input("👤 اسم المستخدم", key="login_user")
    password = st.text_input("🔑 كلمة المرور", type="password", key="login_pass")

    if st.button("تسجيل الدخول"):
        # تحقق بسيط (تقدري تربطيه بقاعدة بيانات أو API لاحقاً)
        if username == "admin" and password == "1234":
            st.session_state.user = username
            st.success("✅ تم تسجيل الدخول بنجاح!")
            st.rerun()
        else:
            st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")

# ===== الداشبورد =====
else:
    st.sidebar.write(f"👋 مرحباً، {st.session_state.user}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.user = None
        st.rerun()

    # ===== Fetch filtered data =====
    try:
        r = requests.get(f"{API}/filter/filter/data")
        r.raise_for_status()
        dff = pd.DataFrame(r.json())

        if not dff.empty:
            dff["purchase_time"] = pd.to_datetime(dff["purchase_time"])

            # ===== KPIs =====
            total_sales = float(dff["total"].sum()) if "total" in dff.columns else 0.0
            tickets_count = len(dff)
            unique_customers = dff["customer_id"].nunique() if "customer_id" in dff.columns else 0
            unique_theaters = dff["theater_id"].nunique() if "theater_id" in dff.columns else 0
            unique_movies = dff["movie_id"].nunique() if "movie_id" in dff.columns else 0

            # العملاء المتكررين
            repeat_customers = (
                dff["customer_id"].value_counts().gt(1).sum()
                if "customer_id" in dff.columns else 0
            )
            repeat_ratio = (repeat_customers / unique_customers * 100) if unique_customers > 0 else 0

            # تقسيم الأعمدة
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} SAR")
            col2.metric("🎟️ عدد التذاكر", tickets_count)
            col3.metric("👥 عدد العملاء", unique_customers)
            col4.metric("🏢 عدد الصالات", unique_theaters)
            col5.metric("🎬 عدد الأفلام", unique_movies)
            col6.metric("🔄 العملاء المتكررين", f"{repeat_customers} ({repeat_ratio:.1f}%)")

            # ===== Tabs =====
            tab1, tab2, tab3 = st.tabs(["🎬 الأفلام", "👥 العملاء", "📅 الإيرادات"])

            with tab1:
                st.subheader("🎬 أفضل 5 أفلام")
                if "Title" in dff.columns and "total" in dff.columns:
                    top_movies = (
                        dff.groupby("Title")["total"].sum()
                        .sort_values(ascending=False)
                        .reset_index()
                        .head(5)
                    )
                    fig = px.bar(
                        top_movies,
                        x="Title",
                        y="total",
                        title="🎬 أفضل 5 أفلام",
                        text_auto=True,
                        color="Title",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📋 عرض التفاصيل"):
                        st.dataframe(top_movies, use_container_width=True)

            with tab2:
                st.subheader("👥 أفضل العملاء")
                if "name_y" in dff.columns and "total" in dff.columns:
                    top_customers = (
                        dff.groupby("name_y")["total"].sum()
                        .sort_values(ascending=False)
                        .reset_index()
                        .head(5)
                    )
                    fig2 = px.pie(
                        top_customers,
                        values="total",
                        names="name_y",
                        color="name_y",
                        color_discrete_sequence=px.colors.qualitative.Set2,
                        title="👥 أفضل 5 عملاء",
                        hole=0.1,
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    with st.expander("📋 عرض التفاصيل"):
                        st.dataframe(top_customers, use_container_width=True)

            with tab3:
                st.subheader("📅 الإيرادات اليومية")
                if "purchase_time" in dff.columns and "total" in dff.columns:
                    daily_rev = dff.groupby("purchase_time")["total"].sum().reset_index()
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
            st.warning("⚠️ لا توجد بيانات مطابقة للفلاتر الحالية.")

    except Exception as e:
        st.error(f"⚠️ خطأ في الاتصال بالـ API: {e}")
        dff = pd.DataFrame()
