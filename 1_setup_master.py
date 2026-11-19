import pandas as pd
from sqlalchemy import create_engine

# 1. Koneksi ke PostgreSQL Lokal
DB_URL = "postgresql://kanechen@localhost:5432/dwh_tribangun"
engine = create_engine(DB_URL)

print("Connecting to PostgreSQL...")

# 2. Data Master Dim_Segmen (Presisi Tabel 2.15 Skripsi)
data_segmen = [
    {
        "sk_segmen": 1,
        "nama_segmen": "Pelanggan Inti",
        "peringkat_segmen": 1,
        "centroid_recency": None,
        "centroid_frequency": None,
        "centroid_monetary": None,
    },
    {
        "sk_segmen": 2,
        "nama_segmen": "Pelanggan Rutin",
        "peringkat_segmen": 2,
        "centroid_recency": None,
        "centroid_frequency": None,
        "centroid_monetary": None,
    },
    {
        "sk_segmen": 3,
        "nama_segmen": "Pelanggan Proyek Besar",
        "peringkat_segmen": 3,
        "centroid_recency": None,
        "centroid_frequency": None,
        "centroid_monetary": None,
    },
    {
        "sk_segmen": 4,
        "nama_segmen": "Pelanggan Baru",
        "peringkat_segmen": 4,
        "centroid_recency": None,
        "centroid_frequency": None,
        "centroid_monetary": None,
    },
    {
        "sk_segmen": 5,
        "nama_segmen": "Pelanggan Pasif",
        "peringkat_segmen": 5,
        "centroid_recency": None,
        "centroid_frequency": None,
        "centroid_monetary": None,
    },
]

df_segmen = pd.DataFrame(data_segmen)
df_segmen.to_sql(
    "dim_segmen", engine, if_exists="append", index=False, method="multi"
)
print("Dim_Segmen (5 Segmen Resmi Tabel 2.15) berhasil terisi!")

# 3. Data Master Dim_Waktu (Presisi 7 Titik Potret Tabel 2.14)
data_waktu = [
    {
        "sk_waktu": 20241231,
        "tanggal": "2024-12-31",
        "bulan": 12,
        "kuartal": 4,
        "tahun": 2024,
        "flag_akhir_kuartal": True,
    },
    {
        "sk_waktu": 20250331,
        "tanggal": "2025-03-31",
        "bulan": 3,
        "kuartal": 1,
        "tahun": 2025,
        "flag_akhir_kuartal": True,
    },
    {
        "sk_waktu": 20250630,
        "tanggal": "2025-06-30",
        "bulan": 6,
        "kuartal": 2,
        "tahun": 2025,
        "flag_akhir_kuartal": True,
    },
    {
        "sk_waktu": 20250930,
        "tanggal": "2025-09-30",
        "bulan": 9,
        "kuartal": 3,
        "tahun": 2025,
        "flag_akhir_kuartal": True,
    },
    {
        "sk_waktu": 20251231,
        "tanggal": "2025-12-31",
        "bulan": 12,
        "kuartal": 4,
        "tahun": 2025,
        "flag_akhir_kuartal": True,
    },
    {
        "sk_waktu": 20260331,
        "tanggal": "2026-03-31",
        "bulan": 3,
        "kuartal": 1,
        "tahun": 2026,
        "flag_akhir_kuartal": True,
    },
    {
        "sk_waktu": 20260630,
        "tanggal": "2026-06-30",
        "bulan": 6,
        "kuartal": 2,
        "tahun": 2026,
        "flag_akhir_kuartal": True,
    },
]

df_waktu = pd.DataFrame(data_waktu)
df_waktu.to_sql(
    "dim_waktu", engine, if_exists="append", index=False, method="multi"
)
print("Dim_Waktu (7 Titik Potret Tabel 2.14) berhasil terisi!")
print("\nSelesai! Data master 100% valid sesuai skripsi.")