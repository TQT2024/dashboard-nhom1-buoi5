import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KHỐI 1: CẤU HÌNH GIAO DIỆN (UI/UX) ---
# Thiết lập trang rộng toàn màn hình và tiêu đề tab trình duyệt
st.set_page_config(page_title="Hệ thống Phân tích GPA", layout="wide")

# Nhúng mã CSS để tùy chỉnh cỡ chữ và kiểu dáng thẻ KPI (Dành cho trình chiếu trên máy chiếu)
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.1rem !important; }
    /* Thiết kế thẻ KPI: Viền đậm, màu xanh Navy, bóng đổ để tạo chiều sâu */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #1a5276;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.1);
    }
    .main-title {
        color: #1a5276;
        font-size: 2.8rem !important;
        font-weight: 900;
        text-align: center;
        margin-bottom: 30px;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

NAVY_BLUE = "#1a5276" # Màu chủ đạo cho báo cáo học thuật

# --- KHỐI 2: XỬ LÝ DỮ LIỆU LÕI (MODEL) ---
@st.cache_data # Lưu dữ liệu vào bộ nhớ đệm để Dashboard chạy mượt, không nạp lại file Excel mỗi khi lọc
def load_data():
    df = pd.read_excel('Database paper.xlsx')
    df.columns = df.columns.str.strip() # Xóa khoảng trắng tên cột để tránh lỗi truy xuất
    
    # Chỉ giữ lại các cột cần thiết cho nghiên cứu để tối ưu tốc độ xử lý
    cols = ['Year', 'GPA', 'Time_Studying', 'Gender', 'Adapt_Learning_Uni', 'Time_SocicalMedia']
    df = df.dropna(subset=cols)

    # Ánh xạ số (1,2,3...) thành Nhãn chữ để Dashboard dễ hiểu đối với con người
    ym = {1: 'Năm 1', 2: 'Năm 2', 3: 'Năm 3', 4: 'Năm 4', 5: 'Đã tốt nghiệp'}
    sm = {1: '< 2h', 2: '2-4h', 3: '4-6h', 4: '6-8h', 5: '> 8h'}
    am = {1: 'Rất kém', 2: 'Kém', 3: 'T.Bình', 4: 'Khá', 5: 'Tốt'}

    df['Year_Label'] = df['Year'].map(ym)
    df['Time_Label'] = df['Time_Studying'].map(sm)
    df['Gender_Label'] = df['Gender'].map({1: 'Nam', 2: 'Nữ'})
    df['Adapt_Label'] = df['Adapt_Learning_Uni'].map(am)
    
    return df, list(ym.values()), list(sm.values()), list(am.values())

df_main, y_order, s_order, a_order = load_data()

# --- KHỐI 3: BỘ ĐIỀU KHIỂN (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Cấu hình")
    gender_filter = st.selectbox("Lọc Giới tính", ["Tất cả", "Nam", "Nữ"])
    # Ghi chú minh bạch về việc xử lý dữ liệu cho Hội đồng/Giảng viên
    st.caption("* Ghi chú: Biểu đồ Sunburst đã được lọc bỏ các nhóm có < 5 sinh viên để loại bỏ nhiễu thống kê.")

# Lọc dữ liệu dựa trên lựa chọn của người dùng
df_filtered = df_main if gender_filter == "Tất cả" else df_main[df_main['Gender_Label'] == gender_filter]

st.markdown("<h1 class='main-title'>PHÂN TÍCH KẾT QUẢ HỌC TẬP</h1>", unsafe_allow_html=True)

if df_filtered.empty:
    st.warning("⚠️ Không có dữ liệu phù hợp với bộ lọc.")
else:
    # --- KHỐI 4: THẺ CHỈ SỐ KPI (CÁCH B - CHỈ SỐ KHÁ/GIỎI) ---
    k1, k2, k3 = st.columns(3)
    
    # Tính toán tỷ lệ Khá/Giỏi: Những người có mã GPA >= 4 (Mức 4: Giỏi, Mức 5: Xuất sắc)
    total_count = len(df_filtered)
    good_excellent_count = len(df_filtered[df_filtered['GPA'] >= 4])
    ratio_good = (good_excellent_count / total_count * 100) if total_count > 0 else 0

    k1.metric("TỔNG SINH VIÊN", f"{total_count:,} SV")
    k2.metric("TỶ LỆ KHÁ/GIỎI", f"{ratio_good:.1f}%")
    k3.metric("MỨC THÍCH NGHI (MODE)", df_filtered['Adapt_Label'].mode()[0])

    st.write("")

    # Hàm chuẩn hóa giao diện biểu đồ (Font to, đậm cho máy chiếu)
    def update_chart_style(fig):
        fig.update_layout(
            template='plotly_white',
            font=dict(size=16, color="black"),
            title_font=dict(size=20, color="#1a5276"),
            margin=dict(t=60, b=40, l=40, r=40)
        )
        return fig

    # --- KHỐI 5: BIỂU ĐỒ BAR & LINE (PHÂN TÍCH XU HƯỚNG) ---
    c1, c2 = st.columns(2)
    with c1:
        df_bar = df_filtered.groupby('Year_Label', observed=True)['GPA'].mean().reset_index()
        df_bar['Year_Label'] = pd.Categorical(df_bar['Year_Label'], categories=y_order, ordered=True)
        fig_bar = px.bar(df_bar.sort_values('Year_Label'), x='Year_Label', y='GPA', 
                         text_auto='.2f', title="<b>Mức GPA trung bình theo Năm học</b>",
                         color_discrete_sequence=[NAVY_BLUE])
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(update_chart_style(fig_bar), use_container_width=True)

    with c2:
        df_line = df_filtered.groupby('Time_Label', observed=True)['GPA'].mean().reset_index()
        df_line['Time_Label'] = pd.Categorical(df_line['Time_Label'], categories=s_order, ordered=True)
        fig_line = px.line(df_line.sort_values('Time_Label'), x='Time_Label', y='GPA', 
                           markers=True, title="<b>Mối liên hệ giữa Thời gian tự học & GPA</b>")
        fig_line.update_traces(line=dict(color=NAVY_BLUE, width=4), marker=dict(size=12))
        st.plotly_chart(update_chart_style(fig_line), use_container_width=True)

    # --- KHỐI 6: MA TRẬN TƯƠNG QUAN (ÁP DỤNG SPEARMAN CHO BIẾN THỨ BẬC) ---
    c3, c4 = st.columns(2)
    with c3:
        # Quan trọng: Dùng method='spearman' vì dữ liệu GPA, TG Học đều là biến thứ bậc (rank-order)
        df_corr = df_filtered[['Time_Studying', 'Time_SocicalMedia', 'Adapt_Learning_Uni', 'GPA']].corr(method='spearman')
        fig_heat = px.imshow(df_corr, text_auto='.2f', color_continuous_scale="Blues",
                             title="<b>Ma trận tương quan Spearman (Phân tích yếu tố)</b>",
                             x=['TG Tự học', 'TG lướt Web', 'Thích nghi', 'GPA'],
                             y=['TG Tự học', 'TG lướt Web', 'Thích nghi', 'GPA'])
        st.plotly_chart(update_chart_style(fig_heat), use_container_width=True)

    # --- KHỐI 7: BIỂU ĐỒ SUNBURST (LỌC NHIỄU & KHÓA MÀU) ---
    with c4:
        df_sun = df_filtered.groupby(['Year_Label', 'Adapt_Label'], observed=True)['GPA'].agg(so_luong='count', gpa_tb='mean').reset_index()
        
        # Kỹ thuật xử lý dữ liệu: Loại bỏ các nhóm quá nhỏ (< 5 SV) để tránh phân mảnh biểu đồ
        df_sun = df_sun[df_sun['so_luong'] >= 5].dropna(subset=['gpa_tb'])
        
        fig_sun = px.sunburst(
            df_sun,
            path=['Year_Label', 'Adapt_Label'],
            values='so_luong',
            color='gpa_tb',
            color_continuous_scale="Blues",
            range_color=[1, 5], # Khóa cứng dải màu từ mức 1 đến mức 5 theo Codebook
            title="<b>Phân cấp: Quy mô Sinh viên & GPA theo Thích nghi</b>"
        )
        fig_sun.update_traces(hovertemplate="<b>%{label}</b><br>Số lượng: %{value} SV<br>Mức GPA: %{color:.2f}")
        fig_sun.update_layout(coloraxis_colorbar=dict(title="Mức GPA"))
        st.plotly_chart(update_chart_style(fig_sun), use_container_width=True)

# --- KHỐI 8: KẾT LUẬN & FOOTER ---
st.markdown("---")
st.markdown("### 📖 TÓM TẮT PHÁT HIỆN TỪ DỮ LIỆU")
st.info(
"""1. **Về GPA:** Tỷ lệ sinh viên đạt mức Khá/Giỏi chiếm ưu thế, đặc biệt là nhóm sinh viên năm cuối.
2. **Về Thích nghi:** Mức độ thích nghi với môi trường đại học có tương quan thuận rõ rệt với GPA.
3. **Về Tác động tiêu cực:** Thời gian sử dụng mạng xã hội (Social Media) có xu hướng làm giảm hiệu suất học tập.
4. **Về Hành vi:** Tăng thời lượng tự học mỗi ngày giúp cải thiện đáng kể điểm số trung bình tích lũy."""
)
st.caption("© 2026 Nhóm nghiên cứu NCKH - Hệ thống Phân tích Dữ liệu Sinh viên")
