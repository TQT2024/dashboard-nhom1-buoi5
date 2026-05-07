import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Học Thuật", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel('Database paper.xlsx')
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Year', 'GPA', 'Time_Studying', 'Gender', 'Adapt_Learning_Uni', 'Time_SocicalMedia'])
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

st.markdown("<h3 style='text-align: center;'>DASHBOARD PHÂN TÍCH KẾT QUẢ HỌC TẬP SINH VIÊN</h3>", unsafe_allow_html=True)

gender_filter = st.selectbox("Bộ lọc Giới tính", ["Tất cả", "Nam", "Nữ"])

df_filtered = df_main if gender_filter == "Tất cả" else df_main[df_main['Gender_Label'] == gender_filter]

if df_filtered.empty:
    st.warning("Không có dữ liệu cho hệ thống lọc hiện tại.")
else:
    kpi1, kpi2 = st.columns(2)
    kpi1.metric("Số lượng Sinh viên", f"{len(df_filtered):,}")
    kpi2.metric("GPA Trung bình", f"{df_filtered['GPA'].mean():.2f}")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        df_bar = df_filtered.groupby('Year_Label', observed=True)['GPA'].mean().reset_index()
        df_bar['Year_Label'] = pd.Categorical(df_bar['Year_Label'], categories=y_order, ordered=True)
        df_bar = df_bar.sort_values('Year_Label')
        fig_bar = px.bar(df_bar, x='Year_Label', y='GPA', text='GPA', title="So sánh GPA theo Năm học", color_discrete_sequence=['#3498db'])
        fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
        fig_bar.update_layout(template='plotly_white', yaxis_range=[0, 4.0], margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_chart2:
        df_line = df_filtered.groupby('Time_Label', observed=True)['GPA'].mean().reset_index()
        df_line['Time_Label'] = pd.Categorical(df_line['Time_Label'], categories=s_order, ordered=True)
        df_line = df_line.sort_values('Time_Label')
        fig_line = px.line(df_line, x='Time_Label', y='GPA', markers=True, title="Xu hướng GPA theo Thời gian tự học")
        fig_line.update_traces(line=dict(color='#2ecc71', width=3), marker=dict(size=8, color='#27ae60'))
        fig_line.update_layout(template='plotly_white', yaxis_range=[0, 4.0], margin=dict(t=40, b=10, l=10, r=10))
        st.plotly_chart(fig_line, use_container_width=True)

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        df_corr = df_filtered[['Time_Studying', 'Time_SocicalMedia', 'Adapt_Learning_Uni', 'GPA']].corr()
        fig_heat = px.imshow(df_corr, x=['TG Tự học', 'TG Lướt Web', 'Thích nghi', 'Điểm GPA'], y=['TG Tự học', 'TG Lướt Web', 'Thích nghi', 'Điểm GPA'], text_auto='.2f', aspect="auto", color_continuous_scale='RdYlGn', title="Tương quan Hành vi & Điểm số")
        fig_heat.update_layout(margin=dict(t=40, b=10, l=10, r=10), coloraxis_showscale=False)
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_chart4:
        df_sun = df_filtered.groupby(['Year_Label', 'Adapt_Label'], observed=True)['GPA'].agg(so_luong='count', gpa_tb='mean').reset_index()
        df_sun = df_sun[df_sun['so_luong'] > 0].dropna(subset=['gpa_tb'])
        df_sun['Year_Label'] = pd.Categorical(df_sun['Year_Label'], categories=y_order, ordered=True)
        df_sun['Adapt_Label'] = pd.Categorical(df_sun['Adapt_Label'], categories=a_order, ordered=True)
        df_sun = df_sun.sort_values(['Year_Label', 'Adapt_Label'])
        fig_sun = px.sunburst(df_sun, path=['Year_Label', 'Adapt_Label'], values='so_luong', color='gpa_tb', range_color=[g_min, g_max], color_continuous_scale='RdYlGn', title="Phân cấp: Quy mô sinh viên & GPA")
        fig_sun.update_traces(insidetextorientation='radial', leaf=dict(opacity=0.9), marker=dict(line=dict(color='#FFFFFF', width=1.5)), hovertemplate="<b>%{label}</b><br>Số lượng: %{value} SV<br>GPA: %{color:.2f}<extra></extra>", textfont=dict(size=12), sort=False)
        fig_sun.update_layout(margin=dict(t=40, l=10, r=10, b=10), coloraxis_colorbar=dict(title="GPA", thickness=10, len=0.7, yanchor="middle", y=0.5, ticks="outside"), uniformtext=dict(minsize=9, mode='hide'))
        st.plotly_chart(fig_sun, use_container_width=True)