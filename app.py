import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="🎬 نظام السينما", layout="wide")

API = "https://cinema-dashboard-2.onrender.com"  # رابط الـ API
from users_db import init_db, add_user, get_user

# أول ما يبدأ التطبيق
init_db()
# مستخدم افتراضي
add_user("admin", "123")

# =================== حالة تسجيل الدخول ===================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state.username = ""

# =================== تسجيل الدخول ===================
if not st.session_state["logged_in"]:
    st.title("🎬 نظام السينما - تسجيل الدخول")

    tab1, tab2 = st.tabs(["🔑 تسجيل الدخول", "📝 تسجيل جديد"])

    with tab1:
        username = st.text_input("اسم المستخدم", key="login_user")
        password = st.text_input("كلمة المرور", type="password", key="login_pass")

        if st.button("دخول", key="login_btn"):
            user = get_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.success("✅ تم تسجيل الدخول بنجاح")
            st.rerun()
        else:
            st.error("❌ بيانات الدخول غير صحيحة")

    with tab2:
        new_user = st.text_input("اسم المستخدم الجديد", key="reg_user")
        new_pass = st.text_input("كلمة المرور", type="password", key="reg_pass")

        if st.button("تسجيل", key="reg_btn"):
            st.success(f"✅ تم إنشاء الحساب للمستخدم: {new_user}")

# =================== الداشبورد ===================
else:
   
    st.sidebar.success(f"مرحباً، {username}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.title("🎬 لوحة مؤشرات دور السينما")

    try:
        r = requests.get(f"{API}/filter/filter/data")
        r.raise_for_status()
        dff = pd.DataFrame(r.json())
        dff["purchase_time"] = pd.to_datetime(dff["purchase_time"])

        # KPIs
        total_sales = float(dff["total"].sum())
        tickets_count = len(dff)
        unique_customers = dff["customer_id"].nunique()
        unique_movies = dff["movie_id"].nunique()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 إجمالي المبيعات", f"{total_sales:,.2f} SAR")
        col2.metric("🎟️ عدد التذاكر", tickets_count)
        col3.metric("👥 العملاء", unique_customers)
        col4.metric("🎬 الأفلام", unique_movies)

        # Top Movies
        st.subheader("🎬 أفضل 5 أفلام")
        top_movies = (
            dff.groupby("Title")["total"].sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(5)
        )
        fig = px.bar(top_movies, x="Title", y="total", text_auto=True, color="Title")
        st.plotly_chart(fig, use_container_width=True)

        # Daily Revenue
        st.subheader("📅 الإيرادات اليومية")
        daily_rev = dff.groupby("purchase_time")["total"].sum().reset_index()
        fig2 = px.line(daily_rev, x="purchase_time", y="total", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ خطأ في الاتصال بالـ API: {e}")
