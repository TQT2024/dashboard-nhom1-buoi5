import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# KHỐI 1: CẤU HÌNH GIAO DIỆN (UI/UX)
# ==========================================
st.set_page_config(page_title="Phân tích dữ liệu học thuật", layout="wide")

# CSS: Tối ưu hiển thị cho báo cáo và trình chiếu trên màn hình lớn
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.05rem !important; }
    /* Định dạng thẻ KPI (Metric) */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dcdcdc;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
    }
    /* Tiêu đề chính của Dashboard */
    .academic-title {
        color: #1a5276;
        font-size: 2.2rem !important;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    /* Tiêu đề biểu đồ tự ngắt dòng */
    .chart-title {
        color: #1a5276;
        font-size: 1.1rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

NAVY_BLUE = "#1a5276"

# ==========================================
# KHỐI 2: TIỀN XỬ LÝ & MÃ HÓA DỮ LIỆU
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_excel('Database paper.xlsx')
    df.columns = df.columns.str.strip()
    
    # Loại bỏ các quan sát thiếu thông tin tại các biến lõi
    cols = ['Year', 'GPA', 'Time_Studying', 'Gender', 'Adapt_Learning_Uni', 'Time_SocicalMedia']
    df = df.dropna(subset=cols)

    # Hệ thống ánh xạ dữ liệu (Codebook Mapping)
    ym = {1: 'Năm 1', 2: 'Năm 2', 3: 'Năm 3', 4: 'Năm 4', 5: 'Đã tốt nghiệp'}
    sm = {1: '< 2h', 2: '2-4h', 3: '4-6h', 4: '6-8h', 5: '> 8h'}
    am = {1: 'Rất kém', 2: 'Kém', 3: 'T.Bình', 4: 'Khá', 5: 'Tốt'}

    df['Year_Label'] = df['Year'].map(ym)
    df['Time_Label'] = df['Time_Studying'].map(sm)
    df['Gender_Label'] = df['Gender'].map({1: 'Nam', 2: 'Nữ'})
    df['Adapt_Label'] = df['Adapt_Learning_Uni'].map(am)
    
    return df, list(ym.values()), list(sm.values()), list(am.values())

df_main, y_order, s_order, a_order = load_data()

# ==========================================
# KHỐI 3: SIDEBAR & BỘ ĐIỀU KHIỂN
# ==========================================
with st.sidebar:
    st.header("Tham số lọc")
    gender_filter = st.selectbox("Phân loại giới tính", ["Tất cả", "Nam", "Nữ"])
    
    st.markdown("---")
    st.markdown("**Chú giải thang đo học lực (GPA):**")
    st.caption("Mức 1: < 2.0 | Mức 2: 2.0-2.5")
    st.caption("Mức 3: 2.5-3.2 | Mức 4: 3.2-3.6")
    st.caption("Mức 5: > 3.6")
    st.markdown("*(TB: Ký hiệu viết tắt cho từ Trung bình)*") # Đã thêm giải nghĩa TB
    
    st.markdown("---")
    st.caption("Ghi chú: Các tổ hợp có n < 5 được lược bỏ trong biểu đồ Sunburst để đảm bảo tính đại diện thống kê.")

# Lọc DataFrame dựa trên lựa chọn
df_filtered = df_main if gender_filter == "Tất cả" else df_main[df_main['Gender_Label'] == gender_filter]

st.markdown("<h1 class='academic-title'>Dashboard phân tích các nhân tố ảnh hưởng đến kết quả học tập của sinh viên</h1>", unsafe_allow_html=True)

if df_filtered.empty:
    st.error("Dữ liệu không tồn tại cho bộ lọc này.")
else:
    # ==========================================
    # KHỐI 4: CHỈ SỐ THỐNG KÊ (KPIs)
    # ==========================================
    k1, k2, k3 = st.columns(3)
    
    total_obs = len(df_filtered)
    # Tính tỷ lệ đạt mức Khá/Giỏi (Mức 4 và 5)
    high_achievers = len(df_filtered[df_filtered['GPA'] >= 4])
    ratio = (high_achievers / total_obs * 100) if total_obs > 0 else 0

    k1.metric("Tổng số quan sát (n)", f"{total_obs:,}")
    k2.metric("Tỷ lệ học lực từ Giỏi trở lên (%)", f"{ratio:.1f}%")
    k3.metric("Mức độ thích nghi phổ biến", df_filtered['Adapt_Label'].mode()[0])

    st.write("")

    # Hàm chuẩn hóa giao diện Plotly (Đã gỡ bỏ tham số title bên trong Plotly)
    def apply_academic_style(fig):
        fig.update_layout(
            template='plotly_white',
            font=dict(size=13, color="black"),
            margin=dict(t=20, b=40, l=40, r=40) # Giảm lề trên vì Streamlit đã lo phần Text
        )
        return fig

    # ==========================================
    # KHỐI 5: BIỂU ĐỒ TRỤC TỌA ĐỘ (BAR & LINE)
    # ==========================================
    c1, c2 = st.columns(2)
    with c1:
        # Giao việc hiển thị Tiêu đề cho Streamlit (tự động ngắt dòng nếu quá dài)
        st.markdown("<div class='chart-title'>Phân phối mức học lực trung bình theo tiến trình năm học</div>", unsafe_allow_html=True)
        
        df_bar = df_filtered.groupby('Year_Label', observed=True)['GPA'].mean().reset_index()
        df_bar['Year_Label'] = pd.Categorical(df_bar['Year_Label'], categories=y_order, ordered=True)
        fig_bar = px.bar(df_bar.sort_values('Year_Label'), x='Year_Label', y='GPA', 
                         text_auto='.2f', color_discrete_sequence=[NAVY_BLUE],
                         labels={'Year_Label': 'Năm học', 'GPA': 'Mức học lực TB'})
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(apply_academic_style(fig_bar), use_container_width=True)

    with c2:
        st.markdown("<div class='chart-title'>Xu hướng biến thiên mức học lực theo thời lượng tự học</div>", unsafe_allow_html=True)
        
        df_line = df_filtered.groupby('Time_Label', observed=True)['GPA'].mean().reset_index()
        df_line['Time_Label'] = pd.Categorical(df_line['Time_Label'], categories=s_order, ordered=True)
        fig_line = px.line(df_line.sort_values('Time_Label'), x='Time_Label', y='GPA', 
                           markers=True, labels={'Time_Label': 'Thời lượng tự học', 'GPA': 'Mức học lực TB'})
        fig_line.update_traces(line=dict(color=NAVY_BLUE, width=3))
        st.plotly_chart(apply_academic_style(fig_line), use_container_width=True)

    # ==========================================
    # KHỐI 6: BIỂU ĐỒ PHÂN TÍCH SÂU (HEATMAP & SUNBURST)
    # ==========================================
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<div class='chart-title'>Ma trận hệ số tương quan Spearman giữa hành vi và học lực</div>", unsafe_allow_html=True)
        
        # Dùng phương pháp Spearman cho biến thứ bậc
        df_corr = df_filtered[['Time_Studying', 'Time_SocicalMedia', 'Adapt_Learning_Uni', 'GPA']].corr(method='spearman')
        fig_heat = px.imshow(df_corr, text_auto='.2f', color_continuous_scale="Blues",
                             x=['TG Tự học', 'TG lướt Web', 'Thích nghi', 'GPA'],
                             y=['TG Tự học', 'TG lướt Web', 'Thích nghi', 'GPA'])
        st.plotly_chart(apply_academic_style(fig_heat), use_container_width=True)

    with c4:
        st.markdown("<div class='chart-title'>Cấu trúc phân lớp học lực theo tiến trình năm học và khả năng thích nghi</div>", unsafe_allow_html=True)
        
        df_sun = df_filtered.groupby(['Year_Label', 'Adapt_Label'], observed=True)['GPA'].agg(n='count', gpa_mean='mean').reset_index()
        df_sun = df_sun[df_sun['n'] >= 5] # Lọc nhiễu
        
        fig_sun = px.sunburst(
            df_sun, path=['Year_Label', 'Adapt_Label'], values='n', color='gpa_mean',
            color_continuous_scale="Blues", range_color=[1, 5],
            labels={'n': 'Số lượng SV', 'gpa_mean': 'Mức học lực TB'}
        )
        fig_sun.update_traces(hovertemplate="<b>%{label}</b><br>Số lượng: %{value} SV<br>Mức GPA TB: %{color:.2f}")
        st.plotly_chart(apply_academic_style(fig_sun), use_container_width=True)

    # ==========================================
    # KHỐI 7: TỔNG KẾT ĐỘNG (CONTEXTUAL INSIGHTS TỐI ƯU)
    # ==========================================
    st.markdown("---")
    st.markdown(f"### Phân tích kết quả nghiên cứu (Nhóm: {gender_filter})")
    
    # Lấy thông số từ dữ liệu lọc
    avg_gpa = df_filtered['GPA'].mean()
    social_corr = df_corr.loc['Time_SocicalMedia', 'GPA']
    study_corr = df_corr.loc['Time_Studying', 'GPA']
    adapt_mode = df_filtered['Adapt_Label'].mode()[0]

    # Dịch điểm trung bình (của biến thứ bậc) thành mô tả học thuật
    if avg_gpa >= 3.6:
        gpa_text = "đạt mức Giỏi đến Xuất sắc"
    elif avg_gpa >= 3.2:
        gpa_text = "tập trung chủ yếu ở mức Khá đến Giỏi"
    elif avg_gpa >= 2.5:
        gpa_text = "duy trì ổn định ở mức Trung bình đến Khá"
    else:
        gpa_text = "phần lớn ở mức Trung bình trở xuống (Cần cải thiện)"

    social_text = "tác động tiêu cực đáng kể" if social_corr < -0.05 else "chưa thể hiện sự ảnh hưởng tiêu cực rõ rệt"
    study_text = "có mối liên hệ thuận chiều (tích cực)" if study_corr > 0 else "chưa thấy rõ mối liên hệ thuận chiều"

    # Hiển thị insight đã chuẩn hóa
    st.info(f"""
    1. **Về phân phối học lực:** Kết quả học tập của nhóm khảo sát ({gender_filter}) {gpa_text}.
    2. **Về tương quan hành vi:** Thời lượng tự học {study_text} với kết quả học tập (Hệ số Spearman: {study_corr:.2f}). Đồng thời, mức độ thích nghi phổ biến nhất của nhóm này là **{adapt_mode}**.
    3. **Về nhân tố ảnh hưởng:** Thời gian sử dụng mạng xã hội cho thấy {social_text} đến mức học lực tích lũy của sinh viên (Hệ số Spearman: {social_corr:.2f}).
    """)
    
    st.caption(f"Nhom 1 Bai tap buoi 5")
