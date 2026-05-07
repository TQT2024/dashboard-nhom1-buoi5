import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Cấu hình trang & Theme
st.set_page_config(page_title="Hệ thống Phân tích GPA", layout="wide")

# Thiết lập style CSS để tạo hiệu ứng Card chuyên nghiệp
st.markdown("""
    <style>
    .stMetric {
        background-color: #f8f9f9;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2e86c1;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .main-title {
        color: #1a5276;
        font-family: 'Helvetica';
        font-weight: bold;
        text-align: center;
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CẤU HÌNH MÀU SẮC ĐỒNG BỘ ---
PRIMARY_BLUE = "#3498db"
COLOR_SCALE_BLUE = "Blues"

@st.cache_data
def load_data():
    # Đọc dữ liệu
    df = pd.read_excel('Database paper.xlsx')
    df.columns = df.columns.str.strip()
    
    # Làm sạch & Ép kiểu
    cols = ['Year', 'GPA', 'Time_Studying', 'Gender', 'Adapt_Learning_Uni', 'Time_SocicalMedia']
    df = df.dropna(subset=cols)
    df = df[(df['GPA'] >= 0) & (df['GPA'] <= 4.0)]

    # Mappings
    ym = {1: 'Năm 1', 2: 'Năm 2', 3: 'Năm 3', 4: 'Năm 4', 5: 'Đã tốt nghiệp'}
    sm = {1: '< 2 giờ', 2: '2-4 giờ', 3: '4-6 giờ', 4: '6-8 giờ', 5: '> 8 giờ'}
    am = {1: 'Rất kém', 2: 'Kém', 3: 'T.Bình', 4: 'Khá', 5: 'Tốt'}

    df['Year_Label'] = df['Year'].map(ym)
    df['Time_Label'] = df['Time_Studying'].map(sm)
    df['Gender_Label'] = df['Gender'].map({1: 'Nam', 2: 'Nữ'})
    df['Adapt_Label'] = df['Adapt_Learning_Uni'].map(am)
    
    return df, list(ym.values()), list(sm.values()), list(am.values())

# 2. Xử lý logic dữ liệu
df_main, y_order, s_order, a_order = load_data()

# --- SIDEBAR: Nơi đặt bộ lọc ---
with st.sidebar:
    st.image("https://flaticon.com", width=100)
    st.title("Bộ lọc dữ liệu")
    gender_filter = st.selectbox("Chọn Giới tính", ["Tất cả", "Nam", "Nữ"])
    st.info("💡 Dashboard cập nhật tự động theo bộ lọc.")

# Lọc dữ liệu
df_filtered = df_main if gender_filter == "Tất cả" else df_main[df_main['Gender_Label'] == gender_filter]

# --- MAIN CONTENT ---
st.markdown("<h1 class='main-title'>DASHBOARD PHÂN TÍCH KẾT QUẢ HỌC TẬP</h1>", unsafe_allow_html=True)

if df_filtered.empty:
    st.warning("⚠️ Không có dữ liệu phù hợp.")
else:
    # 3. KPI Section
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Tổng sinh viên", f"{len(df_filtered):,}")
    kpi2.metric("GPA Trung bình", f"{df_filtered['GPA'].mean():.2f}")
    kpi3.metric("Tỷ lệ phản hồi", f"{(len(df_filtered)/len(df_main)*100):.1f}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- HÀNG BIỂU ĐỒ 1 ---
    col1, col2 = st.columns(2)

    with col1:
        # Bar Chart: Năm học
        df_bar = df_filtered.groupby('Year_Label', observed=True)['GPA'].mean().reset_index()
        df_bar['Year_Label'] = pd.Categorical(df_bar['Year_Label'], categories=y_order, ordered=True)
        df_bar = df_bar.sort_values('Year_Label')
        
        fig_bar = px.bar(df_bar, x='Year_Label', y='GPA', text_auto='.2f',
                         title="<b>Biến động GPA theo Năm học</b>",
                         color_discrete_sequence=[PRIMARY_BLUE])
        fig_bar.update_layout(template='plotly_white', yaxis_range=[0, 4.5], margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # Line Chart: Thời gian tự học
        df_line = df_filtered.groupby('Time_Label', observed=True)['GPA'].mean().reset_index()
        df_line['Time_Label'] = pd.Categorical(df_line['Time_Label'], categories=s_order, ordered=True)
        df_line = df_line.sort_values('Time_Label')
        
        fig_line = px.line(df_line, x='Time_Label', y='GPA', markers=True,
                           title="<b>Mối liên hệ Thời gian học & GPA</b>")
        fig_line.update_traces(line=dict(color=PRIMARY_BLUE, width=4), marker=dict(size=12, color="#1a5276", line=dict(width=2, color="white")))
        fig_line.update_layout(template='plotly_white', yaxis_range=[0, 4.5])
        st.plotly_chart(fig_line, use_container_width=True)

    # --- HÀNG BIỂU ĐỒ 2 ---
    col3, col4 = st.columns(2)

    with col3:
        # Heatmap: Tương quan
        df_corr = df_filtered[['Time_Studying', 'Time_SocicalMedia', 'Adapt_Learning_Uni', 'GPA']].corr()
        fig_heat = px.imshow(df_corr, 
                             x=['Học tập', 'Mạng xã hội', 'Thích nghi', 'GPA'], 
                             y=['Học tập', 'Mạng xã hội', 'Thích nghi', 'GPA'], 
                             text_auto='.2f', color_continuous_scale=COLOR_SCALE_BLUE,
                             title="<b>Ma trận tương quan biến số</b>")
        fig_heat.update_layout(margin=dict(t=50, b=20))
        st.plotly_chart(fig_heat, use_container_width=True)

    with col4:
        # Sunburst rút gọn: Năm học -> Thích nghi
        df_sun = df_filtered.groupby(['Year_Label', 'Adapt_Label'], observed=True)['GPA'].agg(
            so_luong='count', gpa_tb='mean').reset_index()
        
        fig_sun = px.sunburst(
            df_sun, path=['Year_Label', 'Adapt_Label'], values='so_luong', 
            color='gpa_tb', color_continuous_scale=COLOR_SCALE_BLUE,
            title="<b>Cơ cấu Sinh viên & Hiệu quả thích nghi (Sunburst rút gọn)</b>"
        )
        fig_sun.update_layout(margin=dict(t=50, l=10, r=10, b=10))
        st.plotly_chart(fig_sun, use_container_width=True)

# 4. Footer & Story Section
st.markdown("---")
st.caption("© 2026 Dashboard Phân tích Dữ liệu Sinh viên.")

# 📖 Câu chuyện dữ liệu
st.markdown("## 📖 Câu chuyện dữ liệu phục vụ ra quyết định")
st.markdown("""
- **Hành vi cá nhân:** Thời gian tự học (*Time_Studying*) có tác động tích cực đến GPA, trong khi mạng xã hội ảnh hưởng yếu.  
- **Yếu tố môi trường:** Chất lượng giảng viên (*Quality_Lecturer*) là yếu tố có hệ số tương quan cao nhất đối với GPA.  
- **Sự khác biệt nhóm:** Sinh viên năm cuối duy trì GPA ổn định hơn, chứng minh quá trình thích nghi hiệu quả.  
- **Giải pháp:** Nhà trường nên tập trung nâng cao chất lượng giảng dạy và tạo không gian tự học tập trung.  
""")

# 👥 Đánh giá người dùng
st.markdown("## 👥 Đánh giá người dùng")
st.markdown("""
- **Người dùng 1:** Nhận xét Heatmap hơi khó đọc trên màn hình nhỏ.  
- **Người dùng 2:** Sunburst phức tạp, khó hiểu khi có nhiều cấp.  
- **Người dùng 3:** Dashboard dễ dùng, nhưng muốn thêm phần giải thích câu chuyện dữ liệu ngay trên giao diện.  

### 🔧
