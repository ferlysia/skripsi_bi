import pandas as pd
from sqlalchemy import create_engine

# 1. Koneksi ke PostgreSQL DWH
DB_URL = "postgresql://kanechen@localhost:5432/dwh_tribangun"
engine = create_engine(DB_URL)

file_faktur = "daftar_faktur_penjualan_pttribangunusah_260723145231.xlsx"

print("Membaca data faktur Accurate untuk Fact_Penjualan...")

# Read Excel dengan header di baris ke-4
df_faktur = pd.read_excel(file_faktur, header=4)

col_no_faktur = "Nomor #"
col_tanggal = "Tanggal"
col_pelanggan = "Pelanggan"
col_total = "Total"

# Pastikan kolom total berupa angka
df_faktur['total_clean'] = pd.to_numeric(df_faktur[col_total], errors='coerce').fillna(0)

# Filter faktur valid (Total > 0)
df_valid = df_faktur[df_faktur['total_clean'] > 0].copy()

# Format tanggal ke YYYY-MM-DD
df_valid['tanggal_clean'] = pd.to_datetime(df_valid[col_tanggal]).dt.strftime('%Y-%m-%d')

# Ambil master dim_pelanggan dari PostgreSQL untuk mapping sk_pelanggan
df_dim_pelanggan = pd.read_sql("SELECT sk_pelanggan, nama_baku FROM dim_pelanggan", engine)
map_pelanggan = dict(zip(df_dim_pelanggan['nama_baku'], df_dim_pelanggan['sk_pelanggan']))

# Mapping sk_pelanggan
df_valid['nama_baku'] = df_valid[col_pelanggan].astype(str).str.strip()
df_valid['sk_pelanggan'] = df_valid['nama_baku'].map(map_pelanggan)

# Susun struktur Fact_Penjualan
df_fact = pd.DataFrame({
    'no_faktur': df_valid[col_no_faktur].astype(str).str.strip(),
    'tanggal': df_valid['tanggal_clean'],
    'sk_pelanggan': df_valid['sk_pelanggan'],
    'total_nominal': df_valid['total_clean']
})

# 2. Insert ke PostgreSQL
print("Memuat data ke Fact_Penjualan...")
df_fact.to_sql("fact_penjualan", engine, if_exists="append", index=False, method="multi")

print(f"Selesai! {len(df_fact)} transaksi faktur berhasil dimuat ke Fact_Penjualan.")