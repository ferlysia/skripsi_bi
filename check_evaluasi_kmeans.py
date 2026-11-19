import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine

# 1. Tarik Data Transaksi untuk Hitung RFM Aktif
engine = create_engine(
    "postgresql://postgres:postgres@localhost:5432/dwh_tribangun"
)

query = """
    SELECT 
        sk_pelanggan,
        EXTRACT(DAY FROM (NOW() - MAX(tanggal))) AS recency,
        COUNT(no_faktur) AS frequency,
        SUM(total_nominal) AS monetary
    FROM fact_penjualan
    GROUP BY sk_pelanggan
"""
df = pd.read_sql(query, engine)

# Filter hanya data aktif (non-null / non-zero)
df_active = df.dropna().copy()

# 2. Scaling Data RFM
scaler = StandardScaler()
X_scaled = scaler.fit_transform(
    df_active[["recency", "frequency", "monetary"]]
)

# 3. Pengujian K=2 sampai K=8
inertia = []
silhouette_scores = []
K_range = range(2, 9)

print("=== HASIL EVALUASI K-MEANS CLUSTERING ===")
for k in K_range:
  kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
  labels = kmeans.fit_predict(X_scaled)

  inertia.append(kmeans.inertia_)
  score = silhouette_score(X_scaled, labels)
  silhouette_scores.append(score)

  print(
      f"Cluster K={k} | Inertia (Elbow): {kmeans.inertia_:.2f} | Silhouette"
      f" Score: {score:.4f}"
  )

# 4. Plot Grafik Elbow & Silhouette
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot Elbow
ax1.plot(K_range, inertia, "bo-", linewidth=2, markersize=8)
ax1.set_xlabel("Jumlah Cluster (K)")
ax1.set_ylabel("Inertia (Within-Cluster Sum of Squares)")
ax1.set_title("Elbow Method for Optimal K")
ax1.grid(True)

# Plot Silhouette
ax2.plot(K_range, silhouette_scores, "ro-", linewidth=2, markersize=8)
ax2.set_xlabel("Jumlah Cluster (K)")
ax2.set_ylabel("Silhouette Score")
ax2.set_title("Silhouette Score Method")
ax2.grid(True)

plt.tight_layout()
plt.show()