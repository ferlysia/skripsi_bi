import pandas as pd
from sqlalchemy import create_engine

# 1. Koneksi ke PostgreSQL DWH
DB_URL = "postgresql://kanechen@localhost:5432/dwh_tribangun"
engine = create_engine(DB_URL)

file_faktur = "daftar_faktur_penjualan_pttribangunusah_260723145231.xlsx"

print("Membaca data faktur Accurate...")

# Read Excel dengan header di baris ke-4 (indeks 4)
df_faktur = pd.read_excel(file_faktur, header=4)

# Ambil nama kolom pasti
col_pelanggan = "Pelanggan"

# Pastikan kolom total/PPN dibaca sebagai angka
col_total = [c for c in df_faktur.columns if "PPN" in str(c) or "Total" in str(c)][0]
df_faktur[col_total] = pd.to_numeric(df_faktur[col_total], errors='coerce').fillna(0)

# Filter faktur valid (Nilai > 0)
df_valid = df_faktur[df_faktur[col_total] > 0]

# Ambil nama unik pelanggan dari faktur valid
raw_names = df_valid[col_pelanggan].dropna().unique()

print(f"Kolom Pelanggan yang dipakai : '{col_pelanggan}'")
print(f"Kolom Total yang dipakai     : '{col_total}'")
print(f"Ditemukan {len(raw_names)} pelanggan unik dari faktur valid.")

# 2. Susun Dataframe Dim_Pelanggan
list_pelanggan = []
for idx, name in enumerate(sorted(raw_names), start=1):
    clean_name = str(name).strip()
    if clean_name and clean_name.lower() != 'nan':
        list_pelanggan.append({
            "sk_pelanggan": idx,
            "id_pelanggan_sumber": f"CUST-{idx:03d}",
            "nama_baku": clean_name,
            "jumlah_varian_nama": 1,
            "status_padanan_master": "Berhasil"
        })

df_dim_pelanggan = pd.DataFrame(list_pelanggan)

# 3. Load ke PostgreSQL
print("Memuat data ke Dim_Pelanggan...")
df_dim_pelanggan.to_sql("dim_pelanggan", engine, if_exists="append", index=False, method="multi")

print(f"Selesai! {len(df_dim_pelanggan)} pelanggan berhasil dimuat ke Dim_Pelanggan.")