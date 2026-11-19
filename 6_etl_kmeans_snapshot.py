import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# 1. Koneksi Database
DB_URL = "postgresql://kanechen@localhost:5432/dwh_tribangun"
engine = create_engine(DB_URL)

print("--- Memulai Proses Sinkronisasi RFM, K-Means (K=3), & Centroid dim_segmen ---")

# 2. Ambil Data
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

# 4. Transformasi Logaritma & Scaling
df_active['f_log'] = np.log1p(df_active['frequency'])
df_active['m_log'] = np.log1p(df_active['monetary'])

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_active[['recency', 'f_log', 'm_log']])

df_active['r_scaled'] = X_scaled[:, 0]
df_active['f_scaled'] = X_scaled[:, 1]
df_active['m_scaled'] = X_scaled[:, 2]

# 5. K-Means Clustering K=3
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

# 6. Pemetaan Centroid Asli (Sebelum Scaling) untuk Dim_Segmen
cluster_stats = df_active.groupby('cluster_raw')[['recency', 'frequency', 'monetary']].mean().reset_index()
cluster_stats = cluster_stats.sort_values(by=['recency', 'monetary'], ascending=[True, False]).reset_index(drop=True)
cluster_stats['sk_segmen'] = range(1, 4)

map_segmen = dict(zip(cluster_stats['cluster_raw'], cluster_stats['sk_segmen']))
df_active['sk_segmen'] = df_active['cluster_raw'].map(map_segmen)

# 7. UPDATE OTOMATIS TABEL DIM_SEGMEN DI DATABASE (Agar Centroid Tidak NULL)
print("Mengupdate nilai Centroid ke tabel dim_segmen...")
with engine.begin() as conn:
    for idx, row in cluster_stats.iterrows():
        s_id = int(idx + 1)  
        c_rec = float(row['recency'])
        c_freq = float(row['frequency'])
        c_mon = float(row['monetary'])
        
        update_query = f"""
            UPDATE dim_segmen 
            SET centroid_recency = {c_rec}, 
                centroid_frequency = {c_freq}, 
                centroid_monetary = {c_mon}
            WHERE sk_segmen = {s_id};
        """
        conn.execute(text(update_query))

# 8. Gabungkan Data Aktif & Tidak Aktif (Inactive diarahkan ke sk_segmen = 3 / Low-Value/Inactive)
df_inactive = df_all[df_all['is_active'] == False].copy()
df_inactive['r_scaled'] = None
df_inactive['f_scaled'] = None
df_inactive['m_scaled'] = None
df_inactive['sk_segmen'] = 3  # Diarahkan ke sk_segmen 3 (Pelanggan Rendah/Berisiko/Inactive)
df_inactive['jarak_ke_centroid'] = None

cols_final = ['sk_waktu', 'sk_pelanggan', 'recency', 'frequency', 'monetary', 
              'r_scaled', 'f_scaled', 'm_scaled', 'sk_segmen', 'jarak_ke_centroid']

df_final = pd.concat([df_active[cols_final], df_inactive[cols_final]], ignore_index=True)

# 9. Insert ke Fact_RFM_Snapshot
print("Memuat data ke Fact_RFM_Snapshot...")
df_final.to_sql("fact_rfm_snapshot", engine, if_exists="replace", index=False, method="multi")

print(f"Selesai! 749 baris snapshot dimuat & Centroid dim_segmen berhasil disinkronkan.")