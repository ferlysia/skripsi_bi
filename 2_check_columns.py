import pandas as pd

# 1. Buka file faktur penjualan Accurate
file_faktur = "daftar_faktur_penjualan_pttribangunusah_260723145231.xlsx"

# 2. Baca 10 baris pertama untuk cek letak header
df = pd.read_excel(file_faktur, nrows=10)

print("--- 10 Baris Pertama File Faktur ---")
print(df.head(10))
print("\n--- Nama-nama Kolom ---")
print(df.columns.tolist())