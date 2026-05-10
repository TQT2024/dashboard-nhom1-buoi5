import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình trang
st.set_page_config(page_title="Hệ thống Phân tích GPA", layout="wide")

# CSS tối ưu cho trình chiếu: Chữ to, đậm, màu sắc tương phản cao
st.markdown("""
    <style>
    /* Phóng to toàn bộ chữ trên giao diện */
    html, body, [class*="st-"] {
        font-size: 1.1rem !important;
    }
    /* Làm nổi bật các thẻ KPI */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #1a5276;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.1);
    }
    /* Chỉnh tiêu đề cực đại */
    .main-title {
        color: #1a5276;
        font-size: 3rem !important;
        font-weight: 900;
        text-align: center;
        margin-bottom: 30px;
        text-transform: uppercase;
    }
    /* Sidebar chữ to dễ chỉnh */
    .css-1d391kg { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CẤU HÌNH MÀU SẮC TƯƠNG PHẢN CAO ---
NAVY_BLUE = "#1a5276"  # Xanh đậm hẳn để nhìn rõ trên máy chiếu
LIGHT_BLUE = "#d4e6f1"
COLOR_SCALE = "Blues"

@st.cache_data
def load_data():
    df = pd.read_excel('Database paper.xlsx')
    df.columns = df.columns.str.strip()
    cols = ['Year', 'GPA', 'Time_Studying', 'Gender', 'Adapt_Learning_Uni', 'Time_SocicalMedia']
    df = df.dropna(subset=cols)
    #df = df[(df['GPA'] >= 0) & (df['GPA'] <= 5)]

    ym = {1: 'Năm 1', 2: 'Năm 2', 3: 'Năm 3', 4: 'Năm 4', 5: 'Đã tốt nghiệp'}
    sm = {1: '< 2h', 2: '2-4h', 3: '4-6h', 4: '6-8h', 5: '> 8h'}
    am = {1: 'Rất kém', 2: 'Kém', 3: 'T.Bình', 4: 'Khá', 5: 'Tốt'}

    df['Year_Label'] = df['Year'].map(ym)
    df['Time_Label'] = df['Time_Studying'].map(sm)
    df['Gender_Label'] = df['Gender'].map({1: 'Nam', 2: 'Nữ'})
    df['Adapt_Label'] = df['Adapt_Learning_Uni'].map(am)
    
    return df, list(ym.values()), list(sm.values()), list(am.values())

df_main, y_order, s_order, a_order = load_data()

with st.sidebar:
    st.header("⚙️ Cấu hình")
    gender_filter = st.selectbox("Lọc Giới tính", ["Tất cả", "Nam", "Nữ"])
    st.markdown("---")
    st.write("Dùng cho trình chiếu hội trường")

df_filtered = df_main if gender_filter == "Tất cả" else df_main[df_main['Gender_Label'] == gender_filter]

st.markdown("<h1 class='main-title'>PHÂN TÍCH KẾT QUẢ GPA</h1>", unsafe_allow_html=True)

if df_filtered.empty:
    st.warning("⚠️ Không có dữ liệu.")
else:
    # 3. KPI Section - Chữ cực to
    k1, k2, k3 = st.columns(3)
    k1.metric("TỔNG SINH VIÊN", f"{len(df_filtered):,}")
    k2.metric("GPA TRUNG BÌNH", f"{df_filtered['GPA'].mean():.2f}")
    k3.metric("TỶ LỆ HIỂN THỊ", f"{(len(df_filtered)/len(df_main)*100):.1f}%")

    st.write("")

    # Hàm chuẩn hóa layout biểu đồ cho trình chiếu
    def update_chart_style(fig):
        fig.update_layout(
            template='plotly_white',
            font=dict(size=18, color="black"), # Tăng font biểu đồ lên 18
            title_font=dict(size=24, color="#1a5276"), # Tiêu đề biểu đồ lên 24
            margin=dict(t=80, b=50, l=50, r=50)
        )
        return fig

    # --- HÀNG BIỂU ĐỒ 1 ---
    c1, c2 = st.columns(2)
    with c1:
        df_bar = df_filtered.groupby('Year_Label', observed=True)['GPA'].mean().reset_index()
        df_bar['Year_Label'] = pd.Categorical(df_bar['Year_Label'], categories=y_order, ordered=True)
        fig_bar = px.bar(df_bar.sort_values('Year_Label'), x='Year_Label', y='GPA', 
                         text_auto='.2f', title="<b>GPA THEO NĂM HỌC</b>",
                         color_discrete_sequence=[NAVY_BLUE],
                         labels={'Year_Label': 'Năm học', 'GPA': 'GPA'})
        fig_bar.update_traces(textfont_size=20, textposition='outside')
        st.plotly_chart(update_chart_style(fig_bar), use_container_width=True)

    with c2:
        df_line = df_filtered.groupby('Time_Label', observed=True)['GPA'].mean().reset_index()
        df_line['Time_Label'] = pd.Categorical(df_line['Time_Label'], categories=s_order, ordered=True)
        fig_line = px.line(df_line.sort_values('Time_Label'), x='Time_Label', y='GPA', 
                           markers=True, title="<b>GPA THEO GIỜ HỌC</b>",
                           labels={'Time_Label': 'Thời lượng học', 'GPA': 'GPA'}
                          )
        fig_line.update_traces(line=dict(color=NAVY_BLUE, width=6), marker=dict(size=15))
        st.plotly_chart(update_chart_style(fig_line), use_container_width=True)

    # --- HÀNG BIỂU ĐỒ 2 ---
    c3, c4 = st.columns(2)
    with c3:
        df_corr = df_filtered[['Time_Studying', 'Time_SocicalMedia', 'Adapt_Learning_Uni', 'GPA']].corr()
        fig_heat = px.imshow(df_corr, text_auto='.2f', color_continuous_scale="Blues",
                             title="<b>Ma trận tương quan giữa các yếu tố ảnh hưởng đến GPA</b>",
                             x=['Thời gian học', 'Thời gian dùng MXH', 'Mức độ thích nghi', 'GPA'], y=['Thời gian học', 'Thời gian dùng MXH', 'Mức độ thích nghi', 'GPA'])
        st.plotly_chart(update_chart_style(fig_heat), use_container_width=True)

    with c4:
        df_pie = df_filtered.groupby('Adapt_Label', observed=True)['GPA'].agg(so_luong='count', gpa_tb='mean').reset_index()
        st.write(df_pie)  # debug
        fig_pie = px.pie(
            df_pie,
            names='Adapt_Label',
            values='so_luong',
            hover_data={'gpa_tb': ':.2f'},
            title="<b>Phân bố sinh viên theo mức độ thích nghi</b>",
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            pull=[0.04]*len(df_pie)
        )
        st.plotly_chart(update_chart_style(fig_pie), use_container_width=True)

# 4. Footer & Story
st.markdown("---")
st.markdown("### 📖 TÓM TẮT KẾT QUẢ")
st.info("1. Chất lượng giảng viên ảnh hưởng lớn nhất đến GPA. \n2. Sinh viên năm cuối có GPA ổn định hơn nhóm mới thích nghi.")
st.caption("© 2026 Hệ thống Dashboard Trình chiếu")
