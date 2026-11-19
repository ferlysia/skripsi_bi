import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sqlalchemy import create_engine

# ==========================================
# BLOK 0: KONFIGURASI HALAMAN & STATE SESI
# ==========================================
st.set_page_config(
    page_title="Dashboard Segmentasi Pelanggan | PT Tri Bangun Usaha Persada",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inisialisasi Status Login dan Navigasi Halaman
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# Styling CSS Kustom (Padding atas ditambah agar tidak kepotong)
st.markdown("""
    <style>
        .main { background-color: #f4f6f9; }
        .block-container { padding-top: 3rem; padding-bottom: 2rem; } /* Diperbesar dari 1.5rem jadi 3rem */
        .zone-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            margin-bottom: 20px;
        }
        .zone-title {
            color: #0f172a;
            font-size: 1.15rem;
            font-weight: 700;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 6px;
            margin-bottom: 15px;
        }
        .kpi-box {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 10px 12px;
            text-align: center;
            height: 85px;
        }
        .kpi-title {
            font-size: 0.7rem;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
        }
        .kpi-value {
            font-size: 1rem;
            color: #0f172a;
            font-weight: 700;
            margin-top: 2px;
        }
        .kpi-sub {
            font-size: 0.65rem;
            color: #0284c7;
            font-weight: 600;
            margin-top: 2px;
        }
        .login-card {
            max-width: 400px;
            margin: 5rem auto;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)

# Koneksi Database DWH PostgreSQL
DB_URL = "postgresql://kanechen@localhost:5432/dwh_tribangun"
@st.cache_resource
def get_engine():
    return create_engine(DB_URL)

engine = get_engine()

@st.cache_data
def load_data():
    query = """
        SELECT 
            s.sk_waktu,
            w.tanggal AS tanggal_potret,
            w.kuartal,
            w.tahun,
            s.sk_pelanggan,
            p.nama_baku AS nama_pelanggan,
            s.recency AS recency_hari,
            s.frequency AS frequency_transaksi,
            s.monetary AS monetary_nilai,
            s.sk_segmen,
            seg.nama_segmen,
            s.jarak_ke_centroid,
            s.sk_segmen_potret_sebelumnya,
            s.status_perpindahan
        FROM fact_rfm_snapshot s
        JOIN dim_waktu w ON s.sk_waktu = w.sk_waktu
        JOIN dim_pelanggan p ON s.sk_pelanggan = p.sk_pelanggan
        LEFT JOIN dim_segmen seg ON s.sk_segmen = seg.sk_segmen
        ORDER BY w.tanggal ASC, s.sk_pelanggan;
    """
    return pd.read_sql(query, engine)

df = load_data()


# ==========================================
# BLOK 1: HALAMAN MASUK (LOGIN PAGE)
# ==========================================
def show_login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #0f172a;'>🔐 Masuk Sistem</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.85rem;'>PT Tri Bangun Usaha Persada — BI Dashboard</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email_input = st.text_input("Surel Perusahaan", placeholder="contoh: admin@tribangun.com")
            password_input = st.text_input("Kata Sandi", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Masuk", use_container_width=True)
            
            if submit_btn:
                if email_input == "admin@tribangun.com" and password_input == "tribangun2026":
                    st.session_state.logged_in = True
                    st.success("Login Berhasil! Mengarahkan ke dashboard...")
                    st.rerun()
                else:
                    st.error("Surel atau kata sandi salah!")
        st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# BLOK 2: HALAMAN RINCIAN PELANGGAN
# ==========================================
def show_rincian_pelanggan():
    if st.button("⬅️ Kembali ke Dashboard Utama"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown("### 📋 Halaman Rincian Pelanggan & Status")
    st.markdown("<p style='color: #64748b; margin-top: -10px;'>Menampilkan rincian metrik RFM, jarak ke centroid, dan status perpindahan per pelanggan.</p>", unsafe_allow_html=True)

    query_detail = """
        SELECT 
            w.tanggal AS tanggal_potret,
            p.nama_baku AS nama_pelanggan,
            COALESCE(seg.nama_segmen, 'Tidak Hadir / Belum Hadir') AS nama_segmen,
            s.recency AS recency_hari,
            s.frequency AS frequency_transaksi,
            s.monetary AS monetary_nilai,
            s.status_perpindahan,
            s.jarak_ke_centroid
        FROM fact_rfm_snapshot s
        JOIN dim_waktu w ON s.sk_waktu = w.sk_waktu
        JOIN dim_pelanggan p ON s.sk_pelanggan = p.sk_pelanggan
        LEFT JOIN dim_segmen seg ON s.sk_segmen = seg.sk_segmen
        ORDER BY w.tanggal DESC, p.nama_baku;
    """
    df_detail = pd.read_sql(query_detail, engine)

    # Filter Tanggal dan Segmen (ditambah kolom ke-3 untuk Search Bar Rincian)
    col_f1, col_f2, col_f3 = st.columns(3)
    tanggal_list = sorted(df_detail['tanggal_potret'].unique(), reverse=True)
    selected_date = col_f1.selectbox("📅 Pilih Tanggal Potret", tanggal_list, key="rincian_tgl")
    
    segmen_list = ["Semua Segmen"] + list(df_detail['nama_segmen'].unique())
    selected_seg = col_f2.selectbox("🏷️ Filter Segmen", segmen_list, key="rincian_seg")

    # Fitur Search Bar di Halaman Rincian
    search_rincian = col_f3.text_input("🔍 Cari Nama Pelanggan", "", key="search_rincian_input")

    df_filtered = df_detail[df_detail['tanggal_potret'] == selected_date]
    if selected_seg != "Semua Segmen":
        df_filtered = df_filtered[df_filtered['nama_segmen'] == selected_seg]
    
    if search_rincian:
        df_filtered = df_filtered[df_filtered['nama_pelanggan'].str.contains(search_rincian, case=False, na=False)]

    df_display = df_filtered[['nama_pelanggan', 'nama_segmen', 'recency_hari', 'frequency_transaksi', 'monetary_nilai', 'status_perpindahan', 'jarak_ke_centroid']].copy()
    df_display.columns = ['Nama Pelanggan', 'Segmen', 'Recency (Hari)', 'Frequency (Faktur)', 'Monetary (Rp)', 'Status Perpindahan', 'Jarak ke Centroid']

    df_display['Monetary (Rp)'] = df_display['Monetary (Rp)'].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "-")
    df_display['Recency (Hari)'] = df_display['Recency (Hari)'].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "-")
    df_display['Frequency (Faktur)'] = df_display['Frequency (Faktur)'].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "-")
    df_display['Jarak ke Centroid'] = df_display['Jarak ke Centroid'].apply(lambda x: f"{x:.4f}" if pd.notnull(x) else "-")

    st.dataframe(df_display, use_container_width=True, hide_index=True, height=450)


# ==========================================
# BLOK 3: HALAMAN DASHBOARD SEGMENTASI UTAMA
# ==========================================
def show_dashboard_page():
    top_col1, top_col2, top_col3 = st.columns([3, 1, 1])
    with top_col1:
        st.markdown("### 📊 Dashboard Segmentasi Pelanggan")
        st.markdown("<p style='color: #64748b; margin-top: -10px;'>PT Tri Bangun Usaha Persada — Analisis Perilaku & Pergerakan Pelanggan B2B</p>", unsafe_allow_html=True)
    with top_col2:
        if st.button("📋 Buka Rincian", use_container_width=True):
            st.session_state.page = "rincian"
            st.rerun()
    with top_col3:
        if st.button("🔒 Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- ZONA 1 ---
    st.markdown('<div class="zone-card">', unsafe_allow_html=True)
    st.markdown('<div class="zone-title">Zona 1: Pemantauan (Indikator Kinerja Utama & Pembanding Kuartal Sebelumnya)</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    tanggal_list = sorted(df['tanggal_potret'].unique(), reverse=True)
    selected_date = col_f1.selectbox("📅 Pilih Tanggal Potret (Snapshot)", tanggal_list)

    tanggal_sorted = sorted(df['tanggal_potret'].unique())
    current_idx = tanggal_sorted.index(selected_date)
    prev_date = tanggal_sorted[current_idx - 1] if current_idx > 0 else None

    df_current = df[df['tanggal_potret'] == selected_date].copy()
    df_prev = df[df['tanggal_potret'] == prev_date].copy() if prev_date else pd.DataFrame()

    segmen_options = ["Semua Segmen"] + list(df['nama_segmen'].dropna().unique())
    selected_segmen = col_f2.selectbox("🏷️ Filter Segmen", segmen_options)

    if selected_segmen != "Semua Segmen":
        df_current = df_current[df_current['nama_segmen'] == selected_segmen]
        if not df_prev.empty:
            df_prev = df_prev[df_prev['nama_segmen'] == selected_segmen]

    search_pelanggan = col_f3.text_input("🔍 Cari Nama Pelanggan", "")
    if search_pelanggan:
        df_current = df_current[df_current['nama_pelanggan'].str.contains(search_pelanggan, case=False, na=False)]

    st.markdown("<br>", unsafe_allow_html=True)

    kpi1_aktif = df_current['recency_hari'].notnull().sum()
    total_terdaftar = 107
    prev_kpi1 = df_prev['recency_hari'].notnull().sum() if not df_prev.empty else 0
    diff_kpi1 = kpi1_aktif - prev_kpi1
    sub_kpi1 = f"Lalu: {prev_kpi1} (Δ {diff_kpi1:+d})" if not df_prev.empty else "Potret Awal"

    dominant_segmen = df_current['nama_segmen'].mode()
    kpi2_text = dominant_segmen[0] if not dominant_segmen.empty else "-"
    prev_dominant = df_prev['nama_segmen'].mode() if not df_prev.empty else pd.Series()
    prev_kpi2_text = prev_dominant[0] if not prev_dominant.empty else "-"
    sub_kpi2 = f"Lalu: {prev_kpi2_text}" if not df_prev.empty else "Potret Awal"

    kpi3_monetary = df_current['monetary_nilai'].sum() / 1_000_000_000
    prev_kpi3 = df_prev['monetary_nilai'].sum() / 1_000_000_000 if not df_prev.empty else 0
    diff_kpi3 = kpi3_monetary - prev_kpi3
    sub_kpi3 = f"Lalu: Rp {prev_kpi3:.1f}M (Δ {diff_kpi3:+.1f}M)" if not df_prev.empty else "Potret Awal"

    total_all_monetary = df['monetary_nilai'].sum()
    kpi4_konsentrasi = (df_current['monetary_nilai'].sum() / total_all_monetary * 100) if total_all_monetary > 0 else 0
    prev_total_mon = df_prev['monetary_nilai'].sum() if not df_prev.empty else 0
    prev_kpi4 = (prev_total_mon / total_all_monetary * 100) if total_all_monetary > 0 else 0
    diff_kpi4 = kpi4_konsentrasi - prev_kpi4
    sub_kpi4 = f"Lalu: {prev_kpi4:.1f}% (Δ {diff_kpi4:+.1f}%)" if not df_prev.empty else "Potret Awal"

    kpi5_pindah = df_current['status_perpindahan'].isin(['Tetap', 'Naik', 'Turun']).sum()
    prev_kpi5 = df_prev['status_perpindahan'].isin(['Tetap', 'Naik', 'Turun']).sum() if not df_prev.empty else 0
    diff_kpi5 = kpi5_pindah - prev_kpi5
    sub_kpi5 = f"Lalu: {prev_kpi5} orang (Δ {diff_kpi5:+d})" if not df_prev.empty else "Potret Awal"

    kpi6_hadir = df_current['status_perpindahan'].isin(['Masuk', 'Kembali', 'Keluar', 'Tidak Hadir']).sum()
    prev_kpi6 = df_prev['status_perpindahan'].isin(['Masuk', 'Kembali', 'Keluar', 'Tidak Hadir']).sum() if not df_prev.empty else 0
    diff_kpi6 = kpi6_hadir - prev_kpi6
    sub_kpi6 = f"Lalu: {prev_kpi6} orang (Δ {diff_kpi6:+d})" if not df_prev.empty else "Potret Awal"

    kc1, kc2, kc3, kc4, kc5, kc6 = st.columns(6)
    with kc1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">KPI-1 Pelanggan Aktif</div><div class="kpi-value">{kpi1_aktif}/{total_terdaftar}</div><div class="kpi-sub">{sub_kpi1}</div></div>', unsafe_allow_html=True)
    with kc2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">KPI-2 Segmen Dominan</div><div class="kpi-value" style="font-size: 0.8rem; margin-top: 3px;">{kpi2_text}</div><div class="kpi-sub">{sub_kpi2}</div></div>', unsafe_allow_html=True)
    with kc3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">KPI-3 Total Omset</div><div class="kpi-value">Rp {kpi3_monetary:.1f}M</div><div class="kpi-sub">{sub_kpi3}</div></div>', unsafe_allow_html=True)
    with kc4:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">KPI-4 Omset</div><div class="kpi-value">{kpi4_konsentrasi:.1f}%</div><div class="kpi-sub">{sub_kpi4}</div></div>', unsafe_allow_html=True)
    with kc5:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">KPI-5 Pindah Segmen</div><div class="kpi-value">{kpi5_pindah} Orang</div><div class="kpi-sub">{sub_kpi5}</div></div>', unsafe_allow_html=True)
    with kc6:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">KPI-6 Status Pelanggan</div><div class="kpi-value">{kpi6_hadir} Orang</div><div class="kpi-sub">{sub_kpi6}</div></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- ZONA 2 ---
    st.markdown('<div class="zone-card">', unsafe_allow_html=True)
    st.markdown('<div class="zone-title">Zona 2: Penelusuran (Komposisi Pelanggan, Nilai Transaksi, & Matriks Perpindahan)</div>', unsafe_allow_html=True)

    col_z1, col_z2, col_z3 = st.columns(3)

    with col_z1:
        st.markdown("##### **Komposisi Pelanggan**")
        comp_data = df_current['nama_segmen'].value_counts().reset_index()
        comp_data.columns = ['Segmen', 'Jumlah']
        if not comp_data.empty:
            fig_c1 = px.bar(comp_data, x='Jumlah', y='Segmen', orientation='h', text_auto=True)
            fig_c1.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                xaxis_title="",
                yaxis_title="",
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_c1, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    with col_z2:
        st.markdown("##### **Nilai Transaksi (Juta Rp)**")
        mon_data = df_current.groupby('nama_segmen')['monetary_nilai'].sum().reset_index()
        mon_data['Monetary (Juta)'] = mon_data['monetary_nilai'] / 1_000_000
        if not mon_data.empty:
            fig_c2 = px.bar(mon_data, x='Monetary (Juta)', y='nama_segmen', orientation='h', text_auto='.1f')
            fig_c2.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                xaxis_title="",
                yaxis_title="",
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_c2, use_container_width=True)
        else:
            st.info("Tidak ada data.")

    with col_z3:
        st.markdown("##### **Matriks Perpindahan Segmen**")
        st.markdown("<p style='font-size: 0.65rem; color: #64748b; margin-top: -5px;'>Y: Kuartal Lalu (Inti, Rutin, Pasif) ➔ X: Kuartal Sekarang</p>", unsafe_allow_html=True)
        
        kategori_urutan = ["Pelanggan Inti", "Pelanggan Rutin", "Pelanggan Pasif"]
        label_pendek = ["Inti", "Rutin", "Pasif"]
        
        segmen_nama_map = {
            1: "Pelanggan Inti",
            2: "Pelanggan Rutin",
            3: "Pelanggan Pasif",
            "Pelanggan Inti": "Pelanggan Inti",
            "Pelanggan Rutin": "Pelanggan Rutin",
            "Pelanggan Pasif": "Pelanggan Pasif"
        }
        
        df_matrix = df_current.copy()
        df_matrix['Kuartal Lalu'] = df_matrix['sk_segmen_potret_sebelumnya'].map(segmen_nama_map)
        df_matrix['Kuartal Sekarang'] = df_matrix['nama_segmen'].map(segmen_nama_map)
        
        matrix_data = pd.crosstab(df_matrix['Kuartal Lalu'], df_matrix['Kuartal Sekarang'])
        matrix_data = matrix_data.reindex(index=kategori_urutan, columns=kategori_urutan, fill_value=0)
        
        fig_heat = px.imshow(
            matrix_data,
            labels=dict(x="Kuartal Sekarang", y="Kuartal Lalu", color="Klien"),
            x=label_pendek,
            y=label_pendek,
            color_continuous_scale="Blues",
            text_auto=True
        )
        fig_heat.update_layout(
            margin=dict(t=15, b=15, l=15, r=15),
            height=280,
            xaxis_title="",
            yaxis_title="",
            font=dict(size=12)
        )
        fig_heat.update_xaxes(tickangle=0)
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- ZONA 3 ---
    st.markdown('<div class="zone-card">', unsafe_allow_html=True)
    st.markdown('<div class="zone-title">Zona 3: Tindak Lanjut (Ringkasan Data Ringkas & Status)</div>', unsafe_allow_html=True)

    df_display = df_current[['nama_pelanggan', 'nama_segmen', 'recency_hari', 'frequency_transaksi', 'monetary_nilai', 'status_perpindahan', 'jarak_ke_centroid']].copy()
    df_display.columns = ['Nama Pelanggan', 'Segmen', 'Recency (Hari)', 'Frequency (Faktur)', 'Monetary (Rp)', 'Status Perpindahan', 'Jarak ke Centroid']

    df_display['Monetary (Rp)'] = df_display['Monetary (Rp)'].apply(lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else "-")
    df_display['Recency (Hari)'] = df_display['Recency (Hari)'].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "-")
    df_display['Frequency (Faktur)'] = df_display['Frequency (Faktur)'].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "-")
    df_display['Jarak ke Centroid'] = df_display['Jarak ke Centroid'].apply(lambda x: f"{x:.4f}" if pd.notnull(x) else "-")

    st.dataframe(df_display, use_container_width=True, hide_index=True, height=300)

    st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# BLOK 4: KONTROL ROUTING AJUAN UTAMA
# ==========================================
if not st.session_state.logged_in:
    show_login_page()
else:
    if st.session_state.page == "dashboard":
        show_dashboard_page()
    elif st.session_state.page == "rincian":
        show_rincian_pelanggan()