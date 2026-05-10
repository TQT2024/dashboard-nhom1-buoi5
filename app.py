import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="Phân tích dữ liệu học thuật", layout="wide")

# CSS: Tối ưu hiển thị cho báo cáo và trình chiếu
st.markdown("""
    <style>
    html, body, [class*="st-"] { font-size: 1.05rem !important; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #dcdcdc;
    }
    .academic-title {
        color: #1a5276;
        font-size: 2.2rem !important;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

NAVY_BLUE = "#1a5276"

@st.cache_data
def load_data():
    # Nạp và chuẩn hóa dữ liệu từ nguồn tệp tin
    df = pd.read_excel('Database paper.xlsx')
    df.columns = df.columns.str.strip()
    
    # Lọc bỏ các quan sát thiếu thông tin tại các biến số định lượng
    cols = ['Year', 'GPA', 'Time_Studying', 'Gender', 'Adapt_Learning_Uni', 'Time_SocicalMedia']
    df = df.dropna(subset=cols)

    # Hệ thống ánh xạ dữ liệu theo Codebook (Dịch mã số sang nhãn định tính)
    ym = {1: 'Năm 1', 2: 'Năm 2', 3: 'Năm 3', 4: 'Năm 4', 5: 'Đã tốt nghiệp'}
    sm = {1: '< 2h', 2: '2-4h', 3: '4-6h', 4: '6-8h', 5: '> 8h'}
    am = {1: 'Rất kém', 2: 'Kém', 3: 'T.Bình', 4: 'Khá', 5: 'Tốt'}

    df['Year_Label'] = df['Year'].map(ym)
    df['Time_Label'] = df['Time_Studying'].map(sm)
    df['Gender_Label'] = df['Gender'].map({1: 'Nam', 2: 'Nữ'})
    df['Adapt_Label'] = df['Adapt_Learning_Uni'].map(am)
    
    return df, list(ym.values()), list(sm.values()), list(am.values())

df_main, y_order, s_order, a_order = load_data()

# --- THANH ĐIỀU KHIỂN (SIDEBAR) ---
with st.sidebar:
    st.header("Tham số lọc")
    gender_filter = st.selectbox("Phân loại giới tính", ["Tất cả", "Nam", "Nữ"])
    
    st.markdown("---")
    st.markdown("**Chú giải thang đo học lực (GPA):**")
    st.caption("Mức 1: < 2.0 | Mức 2: 2.0-2.5")
    st.caption("Mức 3: 2.5-3.2 | Mức 4: 3.2-3.6")
    st.caption("Mức 5: > 3.6")
    st.markdown("---")
    st.caption("Ghi chú: Các tổ hợp có n < 5 được lược bỏ trong biểu đồ Sunburst để đảm bảo tính đại diện.")

# Lọc dữ liệu theo phân loại giới tính
df_filtered = df_main if gender_filter == "Tất cả" else df_main[df_main['Gender_Label'] == gender_filter]

st.markdown("<h1 class='academic-title'>Hệ thống phân tích các nhân tố ảnh hưởng đến kết quả học tập của sinh viên</h1>", unsafe_allow_html=True)

if df_filtered.empty:
    st.error("Dữ liệu không tồn tại cho bộ lọc này.")
else:
    # --- CHỈ SỐ THỐNG KÊ MÔ TẢ (KPIs) ---
    k1, k2, k3 = st.columns(3)
    
    # Tính toán tỷ lệ phần trăm sinh viên đạt mức học lực Giỏi/Xuất sắc (Mức 4 và 5)
    total_obs = len(df_filtered)
    high_achievers = len(df_filtered[df_filtered['GPA'] >= 4])
    ratio = (high_achievers / total_obs * 100) if total_obs > 0 else 0

    k1.metric("Tổng số quan sát (n)", f"{total_obs:,}")
    k2.metric("Tỷ lệ học lực từ Giỏi trở lên (%)", f"{ratio:.1f}%")
    k3.metric("Mức độ thích nghi phổ biến (Yếu vị)", df_filtered['Adapt_Label'].mode()[0])

    st.write("")

    def apply_academic_style(fig, title):
        fig.update_layout(
            title=f"<b>{title}</b>",
            template='plotly_white',
            font=dict(size=13, color="black"),
            title_font=dict(size=17, color="#1a5276"),
            margin=dict(t=60, b=40, l=40, r=40)
        )
        return fig

    # --- HÀNG BIỂU ĐỒ 1: PHÂN PHỐI VÀ BIẾN THIÊN ---
    c1, c2 = st.columns(2)
    with c1:
        df_bar = df_filtered.groupby('Year_Label', observed=True)['GPA'].mean().reset_index()
        df_bar['Year_Label'] = pd.Categorical(df_bar['Year_Label'], categories=y_order, ordered=True)
        fig_bar = px.bar(df_bar.sort_values('Year_Label'), x='Year_Label', y='GPA', 
                         text_auto='.2f', color_discrete_sequence=[NAVY_BLUE],
                         labels={'Year_Label': 'Năm học', 'GPA': 'Mức học lực TB'})
        fig_bar.update_traces(textposition='outside')
        st.plotly_chart(apply_academic_style(fig_bar, "Phân phối mức học lực trung bình theo năm học"), use_container_width=True)

    with c2:
        df_line = df_filtered.groupby('Time_Label', observed=True)['GPA'].mean().reset_index()
        df_line['Time_Label'] = pd.Categorical(df_line['Time_Label'], categories=s_order, ordered=True)
        fig_line = px.line(df_line.sort_values('Time_Label'), x='Time_Label', y='GPA', 
                           markers=True, labels={'Time_Label': 'Thời lượng tự học', 'GPA': 'Mức học lực TB'})
        fig_line.update_traces(line=dict(color=NAVY_BLUE, width=3))
        st.plotly_chart(apply_academic_style(fig_line, "Xu hướng biến thiên mức học lực theo thời lượng tự học"), use_container_width=True)

    # --- HÀNG BIỂU ĐỒ 2: TƯƠNG QUAN VÀ CẤU TRÚC ---
    c3, c4 = st.columns(2)
    with c3:
        # Sử dụng hệ số tương quan Spearman cho các biến số thứ bậc
        df_corr = df_filtered[['Time_Studying', 'Time_SocicalMedia', 'Adapt_Learning_Uni', 'GPA']].corr(method='spearman')
        fig_heat = px.imshow(df_corr, text_auto='.2f', color_continuous_scale="Blues",
                             x=['TG Tự học', 'TG lướt Web', 'Thích nghi', 'GPA'],
                             y=['TG Tự học', 'TG lướt Web', 'Thích nghi', 'GPA'])
        st.plotly_chart(apply_academic_style(fig_heat, "Ma trận hệ số tương quan Spearman giữa các biến số hành vi và học lực"), use_container_width=True)

    with c4:
        df_sun = df_filtered.groupby(['Year_Label', 'Adapt_Label'], observed=True)['GPA'].agg(n='count', gpa_mean='mean').reset_index()
        df_sun = df_sun[df_sun['n'] >= 5]
        
        fig_sun = px.sunburst(
            df_sun, path=['Year_Label', 'Adapt_Label'], values='n', color='gpa_mean',
            color_continuous_scale="Blues", range_color=[1, 5],
            labels={'n': 'Số lượng SV', 'gpa_mean': 'Mức học lực TB'}
        )
        fig_sun.update_traces(hovertemplate="<b>%{label}</b><br>Số lượng: %{value} SV<br>Mức GPA TB: %{color:.2f}")
        st.plotly_chart(apply_academic_style(fig_sun, "Cấu trúc phân lớp học lực theo tiến trình năm học và khả năng thích nghi"), use_container_width=True)

# --- TỔNG KẾT ---
st.markdown("---")
st.markdown("### Phân tích kết quả nghiên cứu")
st.info(
"""1. **Về phân phối học lực:** Kết quả học tập có xu hướng ổn định và đạt mức cao hơn ở giai đoạn sinh viên năm cuối và sau tốt nghiệp.
2. **Về tương quan hành vi:** Thời lượng tự học và khả năng thích nghi môi trường có mối liên hệ thuận chiều với kết quả học tập.
3. **Về nhân tố ảnh hưởng:** Thời gian sử dụng mạng xã hội cho thấy xu hướng tác động tiêu cực đến mức học lực tích lũy của sinh viên."""
)
st.caption("Hệ thống trực quan hóa dữ liệu phục vụ nghiên cứu khoa học - Nhóm 1")
