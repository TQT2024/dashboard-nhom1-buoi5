import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Dashboard Học Thuật", layout="wide")

# --- MÀU CHỦ ĐẠO ---
# Chúng ta sẽ dùng dải màu Blues của Plotly: Xanh nhạt đến Xanh đậm
MAIN_COLOR = "#5dade2" # Xanh biển nhạt
COLOR_SCALE = "Blues"   # Dải màu đồng bộ cho Heatmap và Sunburst

@st.cache_data
def load_data():
    df = pd.read_excel('Database paper.xlsx')
    df.columns = df.columns.str.strip()
    cols_to_check = ['Year', 'GPA', 'Time_Studying', 'Gender', 'Adapt_Learning_Uni', 'Time_SocicalMedia']
    df = df.dropna(subset=cols_to_check)
    df = df[(df['GPA'] >= 0) & (df['GPA'] <= 4.0)]

    ym = {1: 'Năm 1', 2: 'Năm 2', 3: 'Năm 3', 4: 'Năm 4', 5: 'Đã tốt nghiệp'}
    sm = {1: '< 2 giờ', 2: '2 đến < 4 giờ', 3: '4 đến < 6 giờ', 4: '6 đến < 8 giờ', 5: '> 8 giờ'}
    am = {1: 'Rất kém', 2: 'Kém', 3: 'Trung bình', 4: 'Khá', 5: 'Tốt'}

    df['Year_Label'] = df['Year'].map(ym)
    df['Time_Label'] = df['Time_Studying'].map(sm)
    df['Gender_Label'] = df['Gender'].map({1: 'Nam', 2: 'Nữ'})
    df['Adapt_Label'] = df['Adapt_Learning_Uni'].map(am)
    
    gpa_min, gpa_max = round(df['GPA'].min(), 2), round(df['GPA'].max(), 2)
    return df, list(ym.values()), list(sm.values()), list(am.values()), gpa_min, gpa_max

df_main, y_order, s_order, a_order, g_min, g_max = load_data()

# Tiêu đề Dashboard với màu xanh biển
st.markdown(f"<h2 style='text-align: center; color: #2e86c1;'>DASHBOARD PHÂN TÍCH KẾT QUẢ HỌC TẬP SINH VIÊN</h2>", unsafe_allow_html=True)
st.markdown("---")

gender_filter = st.selectbox("Bộ lọc Giới tính", ["Tất cả", "Nam", "Nữ"])
df_filtered = df_main if gender_filter == "Tất cả" else df_main[df_main['Gender_Label'] == gender_filter]

if df_filtered.empty:
    st.warning("Không có dữ liệu.")
else:
    # KPI với style sạch sẽ
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.metric("Số lượng Sinh viên", f"{len(df_filtered):,}")
    with kpi2:
        st.metric("GPA Trung bình", f"{df_filtered['GPA'].mean():.2f}")

    # --- HÀNG BIỂU ĐỒ 1 ---
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        df_bar = df_filtered.groupby('Year_Label', observed=True)['GPA'].mean().reset_index()
        df_bar['Year_Label'] = pd.Categorical(df_bar['Year_Label'], categories=y_order, ordered=True)
        df_bar = df_bar.sort_values('Year_Label')
        
        fig_bar = px.bar(df_bar, x='Year_Label', y='GPA', text='GPA', 
                         title="So sánh GPA theo Năm học", 
                         color_discrete_sequence=[MAIN_COLOR]) # SỬ DỤNG MÀU CHÍNH
        fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_bar.update_layout(template='plotly_white', yaxis_range=[0, 4.5], margin=dict(t=50, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        df_line = df_filtered.groupby('Time_Label', observed=True)['GPA'].mean().reset_index()
        df_line['Time_Label'] = pd.Categorical(df_line['Time_Label'], categories=s_order, ordered=True)
        df_line = df_line.sort_values('Time_Label')
        
        fig_line = px.line(df_line, x='Time_Label', y='GPA', markers=True, 
                           title="Xu hướng GPA theo Thời gian tự học")
        fig_line.update_traces(line=dict(color=MAIN_COLOR, width=4), # ĐỒNG BỘ MÀU ĐƯỜNG
                               marker=dict(size=10, color="#21618c", line=dict(width=2, color='white')))
        fig_line.update_layout(template='plotly_white', yaxis_range=[0, 4.5], margin=dict(t=50, b=10))
        st.plotly_chart(fig_line, use_container_width=True)

    # --- HÀNG BIỂU ĐỒ 2 ---
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        df_corr = df_filtered[['Time_Studying', 'Time_SocicalMedia', 'Adapt_Learning_Uni', 'GPA']].corr()
        # Chuyển sang bảng màu Blues để đồng bộ, bỏ màu Đỏ-Xanh gây rối
        fig_heat = px.imshow(df_corr, 
                             x=['TG Tự học', 'TG Lướt Web', 'Thích nghi', 'Điểm GPA'], 
                             y=['TG Tự học', 'TG Lướt Web', 'Thích nghi', 'Điểm GPA'], 
                             text_auto='.2f', 
                             color_continuous_scale=COLOR_SCALE, # ĐỒNG BỘ DẢI MÀU XANH
                             title="Tương quan Hành vi & Điểm số")
        fig_heat.update_layout(margin=dict(t=50, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_chart4:
        df_sun = df_filtered.groupby(['Year_Label', 'Adapt_Label'], observed=True)['GPA'].agg(
            so_luong='count', gpa_tb='mean').reset_index()
        df_sun = df_sun[df_sun['so_luong'] > 0].dropna()
        
        if not df_sun.empty:
            # Chuyển sang string để tránh lỗi nhánh rỗng
            df_sun['Year_Label'] = df_sun['Year_Label'].astype(str)
            df_sun['Adapt_Label'] = df_sun['Adapt_Label'].astype(str)
            
            fig_sun = px.sunburst(
                df_sun, path=['Year_Label', 'Adapt_Label'], values='so_luong', 
                color='gpa_tb', 
                color_continuous_scale=COLOR_SCALE, # ĐỒNG BỘ DẢI MÀU XANH
                title="Phân cấp: Quy mô sinh viên & GPA"
            )
            fig_sun.update_traces(marker=dict(line=dict(color='#FFFFFF', width=1)))
            fig_sun.update_layout(margin=dict(t=50, l=10, r=10, b=10))
            st.plotly_chart(fig_sun, use_container_width=True)
