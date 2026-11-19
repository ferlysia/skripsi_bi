import pandas as pd

file_faktur = "daftar_faktur_penjualan_pttribangunusah_260723145231.xlsx"

# Skip 3 baris header cetakan laporan Accurate
df = pd.read_excel(file_faktur, header=3)

print("--- Daftar Semua Kolom Bersih ---")
for idx, col in enumerate(df.columns):
    print(f"{idx}: {col}")

print("\n--- 5 Baris Pertama Data Faktur ---")
print(df.head(5))