import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# 1. Koneksi Database
DB_URL = "postgresql://kanechen@localhost:5432/dwh_tribangun"
engine = create_engine(DB_URL)

print("--- Memulai Proses Khusus: Snapshot & Logika 8 Status Perpindahan ---")

# 2. Ambil Data Transaksi dan Master
df_fact = pd.read_sql("SELECT no_faktur, tanggal, sk_pelanggan, total_nominal FROM fact_penjualan", engine)
df_dim_waktu = pd.read_sql("SELECT sk_waktu, tanggal FROM dim_waktu ORDER BY tanggal", engine)
df_dim_pelanggan = pd.read_sql("SELECT sk_pelanggan FROM dim_pelanggan", engine)

df_fact['tanggal'] = pd.to_datetime(df_fact['tanggal'])
df_dim_waktu['tanggal'] = pd.to_datetime(df_dim_waktu['tanggal'])

snapshot_rows = []

# 3. Kalkulasi RFM Jendela Bergulir (12 Bulan) per Titik Snapshot
for _, row_waktu in df_dim_waktu.iterrows():
    sk_waktu = row_waktu['sk_waktu']
    tgl_snapshot = row_waktu['tanggal']
    tgl_mulai = tgl_snapshot - pd.DateOffset(months=12)
    
    df_window = df_fact[(df_fact['tanggal'] > tgl_mulai) & (df_fact['tanggal'] <= tgl_snapshot)]
    
    for sk_p in df_dim_pelanggan['sk_pelanggan']:
        df_p = df_window[df_window['sk_pelanggan'] == sk_p]
        
        if len(df_p) > 0:
            last_tx = df_p['tanggal'].max()
            recency = (tgl_snapshot - last_tx).days
            frequency = len(df_p)
            monetary = float(df_p['total_nominal'].sum())
            is_active = True
        else:
            recency = None
            frequency = 0
            monetary = 0.0
            is_active = False
            
        snapshot_rows.append({
            'sk_waktu': sk_waktu,
            'sk_pelanggan': sk_p,
            'recency': recency,
            'frequency': frequency,
            'monetary': monetary,
            'is_active': is_active
        })

df_all = pd.DataFrame(snapshot_rows)
df_active = df_all[df_all['is_active'] == True].copy()

# 4. Transformasi Logaritma & Scaling untuk K-Means
df_active['f_log'] = np.log1p(df_active['frequency'])
df_active['m_log'] = np.log1p(df_active['monetary'])

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_active[['recency', 'f_log', 'm_log']])

df_active['r_scaled'] = X_scaled[:, 0]
df_active['f_scaled'] = X_scaled[:, 1]
df_active['m_scaled'] = X_scaled[:, 2]

# 5. K-Means Clustering K=3 (Acuan Tetap Sesuai Proposal)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df_active['cluster_raw'] = kmeans.fit_predict(X_scaled)

# Hitung Jarak ke Centroid
centroids = kmeans.cluster_centers_
distances = []
for idx, row in enumerate(X_scaled):
    c_idx = df_active['cluster_raw'].iloc[idx]
    dist = np.linalg.norm(row - centroids[c_idx])
    distances.append(dist)

df_active['jarak_ke_centroid'] = distances

# 6. Pemetaan Urutan Kluster ke sk_segmen (1: Pelanggan Inti, 2: Pelanggan Rutin, 3: Pelanggan Pasif)
cluster_stats = df_active.groupby('cluster_raw')[['recency', 'frequency', 'monetary']].mean().reset_index()
cluster_stats = cluster_stats.sort_values(by=['recency', 'monetary'], ascending=[True, False]).reset_index(drop=True)
cluster_stats['sk_segmen'] = range(1, 4)

map_segmen = dict(zip(cluster_stats['cluster_raw'], cluster_stats['sk_segmen']))
df_active['sk_segmen'] = df_active['cluster_raw'].map(map_segmen)

# 7. Gabungkan Data Aktif & Tidak Aktif
df_inactive = df_all[df_all['is_active'] == False].copy()
df_inactive['r_scaled'] = None
df_inactive['f_scaled'] = None
df_inactive['m_scaled'] = None
df_inactive['sk_segmen'] = 3  # Pelanggan Pasif
df_inactive['jarak_ke_centroid'] = None

cols_final = ['sk_waktu', 'sk_pelanggan', 'recency', 'frequency', 'monetary', 
              'r_scaled', 'f_scaled', 'm_scaled', 'sk_segmen', 'jarak_ke_centroid', 'is_active']

df_final = pd.concat([df_active[cols_final], df_inactive[cols_final]], ignore_index=True)
df_final = df_final.sort_values(by=['sk_pelanggan', 'sk_waktu']).reset_index(drop=True)

# 8. IMPLEMENTASI LOGIKA 8 STATUS PERPINDAHAN ANTAR POTRET
print("Menghitung status perpindahan (Masuk, Naik, Turun, Tetap, Keluar, Kembali, Tidak Hadir, Belum Hadir)...")
df_final['sk_segmen_potret_sebelumnya'] = None
df_final['status_perpindahan'] = None

waktu_list = sorted(df_final['sk_waktu'].unique())

for p_idx, sk_waktunya in enumerate(waktu_list):
    is_first_snapshot = (p_idx == 0)
    mask_current = df_final['sk_waktu'] == sk_waktunya
    
    for idx, row in df_final[mask_current].iterrows():
        p_langgan = row['sk_pelanggan']
        aktif_sekarang = row['is_active']
        segmen_sekarang = row['sk_segmen'] if aktif_sekarang else None
        
        if is_first_snapshot:
            if aktif_sekarang:
                df_final.loc[idx, 'status_perpindahan'] = 'Masuk'
            else:
                df_final.loc[idx, 'status_perpindahan'] = 'Belum Pernah Hadir'
        else:
            prev_waktu = waktu_list[p_idx - 1]
            prev_row = df_final[(df_final['sk_waktu'] == prev_waktu) & (df_final['sk_pelanggan'] == p_langgan)]
            
            if not prev_row.empty:
                prev_aktif = prev_row['is_active'].values[0]
                prev_segmen = prev_row['sk_segmen'].values[0] if prev_aktif else None
                
                df_final.loc[idx, 'sk_segmen_potret_sebelumnya'] = prev_segmen
                
                if not prev_aktif and not aktif_sekarang:
                    df_final.loc[idx, 'status_perpindahan'] = 'Tidak Hadir'
                elif prev_aktif and not aktif_sekarang:
                    df_final.loc[idx, 'status_perpindahan'] = 'Keluar'
                elif not prev_aktif and aktif_sekarang:
                    df_final.loc[idx, 'status_perpindahan'] = 'Kembali'
                elif prev_aktif and aktif_sekarang:
                    # Logika Naik/Turun berdasarkan peringkat segmen (1: Inti, 2: Rutin, 3: Pasif)
                    if segmen_sekarang < prev_segmen:
                        df_final.loc[idx, 'status_perpindahan'] = 'Naik'
                    elif segmen_sekarang > prev_segmen:
                        df_final.loc[idx, 'status_perpindahan'] = 'Turun'
                    else:
                        df_final.loc[idx, 'status_perpindahan'] = 'Tetap'
            else:
                if aktif_sekarang:
                    df_final.loc[idx, 'status_perpindahan'] = 'Masuk'
                else:
                    df_final.loc[idx, 'status_perpindahan'] = 'Belum Pernah Hadir'

# Bersihkan kolom bantu is_active
if 'is_active' in df_final.columns:
    df_final = df_final.drop(columns=['is_active'])

# Konversi tipe data agar bersih menjadi native Python (mencegah error SQLAlchemy parameter binding)
for col in df_final.columns:
    df_final[col] = df_final[col].where(pd.notnull(df_final[col]), None)

integer_cols = ['sk_waktu', 'sk_pelanggan', 'frequency', 'sk_segmen', 'sk_segmen_potret_sebelumnya']
for col in integer_cols:
    if col in df_final.columns:
        df_final[col] = df_final[col].apply(lambda x: int(x) if x is not None else None)

floating_cols = ['recency', 'monetary', 'r_scaled', 'f_scaled', 'm_scaled', 'jarak_ke_centroid']
for col in floating_cols:
    if col in df_final.columns:
        df_final[col] = df_final[col].apply(lambda x: float(x) if x is not None else None)

# 9. Simpan ke Tabel Fact_RFM_Snapshot di TablePlus/PostgreSQL menggunakan chunksize
print("Memuat data akhir ke Fact_RFM_Snapshot...")
df_final.to_sql("fact_rfm_snapshot", engine, if_exists="replace", index=False, method="multi", chunksize=100)

print(f"Selesai! Seluruh data snapshot dan 8 status perpindahan berhasil diproses dan disimpan.")