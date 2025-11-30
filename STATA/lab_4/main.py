import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.metrics import (
    silhouette_score, davies_bouldin_score, calinski_harabasz_score,
    adjusted_rand_score, normalized_mutual_info_score, confusion_matrix,
    silhouette_samples
)
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import dendrogram, linkage
import warnings
warnings.filterwarnings('ignore')

# Configure matplotlib for better output
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print("="*80)
print("STEP 1: LOADING DATA")
print("="*80)

df = pd.read_csv('insurance.csv')

print(f"\n✓ Dataset shape: {df.shape}")
print(f"✓ Data types:\n{df.dtypes}")
print(f"✓ Missing values:\n{df.isnull().sum()}")
print(f"✓ Basic statistics:\n{df.describe()}")

# ============================================================================
# STEP 2: PREPROCESSING FOR CLUSTERING
# ============================================================================

print("\n" + "="*80)
print("STEP 2: DATA PREPROCESSING FOR CLUSTERING")
print("="*80)

# Save original target for validation
print(f"\n✓ Saving original target variable for validation...")
y_true = (df['charges'] > df['charges'].median()).astype(int)
print(f"  True labels (based on charges): {dict(y_true.value_counts())}")

# Prepare features (exclude charges)
X = df.drop(['charges'], axis=1).copy()

print(f"\n✓ Features shape after dropping target: {X.shape}")

# Detect outliers
print(f"\n✓ Outlier detection (IQR method):")
for col in ['age', 'bmi', 'children']:
    Q1 = X[col].quantile(0.25)
    Q3 = X[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = len(X[(X[col] < Q1 - 1.5*IQR) | (X[col] > Q3 + 1.5*IQR)])
    print(f"  {col:10s}: {outliers:3d} outliers ({outliers/len(X)*100:.2f}%)")

# Encode categorical variables
print(f"\n✓ Encoding categorical variables:")
le_sex = LabelEncoder()
le_smoker = LabelEncoder()
le_region = LabelEncoder()

X['sex'] = le_sex.fit_transform(X['sex'])
X['smoker'] = le_smoker.fit_transform(X['smoker'])
X['region'] = le_region.fit_transform(X['region'])

print(f"  sex: {dict(zip(le_sex.classes_, le_sex.transform(le_sex.classes_)))}")
print(f"  smoker: {dict(zip(le_smoker.classes_, le_smoker.transform(le_smoker.classes_)))}")
print(f"  region: {dict(zip(le_region.classes_, le_region.transform(le_region.classes_)))}")

# Scale features
print(f"\n✓ Scaling features (StandardScaler):")
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
print(f"  Features scaled to mean=0, std=1")

# ============================================================================
# STEP 3: KMEANS - FIND OPTIMAL CLUSTERS
# ============================================================================

print("\n" + "="*80)
print("STEP 3.1: KMEANS - ELBOW METHOD & SILHOUETTE ANALYSIS")
print("="*80)

# Elbow Method
print("\n✓ Elbow Method - Finding optimal k:")
inertias = []
silhouette_scores = []
k_range = range(2, 11)

for k in k_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)
    sil_score = silhouette_score(X_scaled, kmeans.labels_)
    silhouette_scores.append(sil_score)
    print(f"  k={k}: Inertia={kmeans.inertia_:.2f}, Silhouette={sil_score:.4f}")

# Find optimal k
optimal_k = k_range[np.argmax(silhouette_scores)]
print(f"\n✓ Optimal k (by Silhouette Score): {optimal_k}")

# Train KMeans with optimal k
print(f"\n✓ Training KMeans with k={optimal_k}...")
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
kmeans_labels = kmeans.fit_predict(X_scaled)

print(f"  KMeans cluster distribution:")
print(f"  {dict(pd.Series(kmeans_labels).value_counts().sort_index())}")

# ============================================================================
# STEP 3.2: AGGLOMERATIVE CLUSTERING
# ============================================================================

print("\n" + "="*80)
print("STEP 3.2: AGGLOMERATIVE CLUSTERING")
print("="*80)

print("\n✓ Testing different linkage methods:")
linkage_methods = ['ward', 'complete', 'average', 'single']
agg_results = {}

for linkage_method in linkage_methods:
    print(f"\n  Linkage: {linkage_method}")
    agg = AgglomerativeClustering(n_clusters=optimal_k, linkage=linkage_method)
    agg_labels = agg.fit_predict(X_scaled)
    
    sil_score = silhouette_score(X_scaled, agg_labels)
    db_index = davies_bouldin_score(X_scaled, agg_labels)
    ch_index = calinski_harabasz_score(X_scaled, agg_labels)
    
    agg_results[linkage_method] = {
        'labels': agg_labels,
        'silhouette': sil_score,
        'db_index': db_index,
        'ch_index': ch_index
    }
    
    print(f"    Silhouette: {sil_score:.4f}")
    print(f"    Davies-Bouldin: {db_index:.4f}")
    print(f"    Calinski-Harabasz: {ch_index:.4f}")

# Select best linkage
best_linkage = max(agg_results, key=lambda x: agg_results[x]['silhouette'])
print(f"\n✓ Best linkage method: {best_linkage}")
agg_labels = agg_results[best_linkage]['labels']

print(f"  Agglomerative cluster distribution:")
print(f"  {dict(pd.Series(agg_labels).value_counts().sort_index())}")

# ============================================================================
# STEP 3.3: DBSCAN
# ============================================================================

print("\n" + "="*80)
print("STEP 3.3: DBSCAN - OPTIMAL PARAMETERS")
print("="*80)

# Find optimal eps using k-distance graph
print("\n✓ Finding optimal eps using k-distance method:")
from sklearn.neighbors import NearestNeighbors

k = 4
neighbors = NearestNeighbors(n_neighbors=k)
neighbors_fit = neighbors.fit(X_scaled)
distances, indices = neighbors_fit.kneighbors(X_scaled)
distances = np.sort(distances[:, k-1], axis=0)

# Test different eps values
eps_values = [0.3, 0.5, 0.7, 1.0, 1.2, 1.5]
min_samples_values = [3, 5, 10]

print(f"\n✓ Testing DBSCAN with different parameters:")
dbscan_results = {}

for eps in eps_values:
    for min_samples in min_samples_values:
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        dbscan_labels = dbscan.fit_predict(X_scaled)
        
        n_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)
        n_outliers = list(dbscan_labels).count(-1)
        
        if n_clusters > 1 and n_outliers < len(X_scaled) * 0.3:
            sil_score = silhouette_score(X_scaled[dbscan_labels != -1], 
                                         dbscan_labels[dbscan_labels != -1])
            
            key = (eps, min_samples)
            dbscan_results[key] = {
                'labels': dbscan_labels,
                'n_clusters': n_clusters,
                'n_outliers': n_outliers,
                'silhouette': sil_score
            }

# Find best DBSCAN
if dbscan_results:
    best_dbscan = max(dbscan_results, 
                      key=lambda x: dbscan_results[x]['silhouette'])
    print(f"\n✓ Best DBSCAN parameters: eps={best_dbscan[0]}, min_samples={best_dbscan[1]}")
    
    dbscan_labels = dbscan_results[best_dbscan]['labels']
    n_clusters_dbscan = dbscan_results[best_dbscan]['n_clusters']
    n_outliers_dbscan = dbscan_results[best_dbscan]['n_outliers']
    
    print(f"  Clusters: {n_clusters_dbscan}")
    print(f"  Outliers: {n_outliers_dbscan} ({n_outliers_dbscan/len(X_scaled)*100:.2f}%)")
    print(f"  Cluster distribution:")
    unique, counts = np.unique(dbscan_labels, return_counts=True)
    for u, c in zip(unique, counts):
        label = f"Outliers" if u == -1 else f"Cluster {u}"
        print(f"    {label}: {c}")
else:
    print("\n⚠️  No suitable DBSCAN parameters found!")
    dbscan_labels = np.full(len(X_scaled), -1)
    n_clusters_dbscan = 0

# ============================================================================
# STEP 4: EVALUATE ALL MODELS
# ============================================================================

print("\n" + "="*80)
print("STEP 4: CLUSTERING QUALITY EVALUATION")
print("="*80)

results_table = []

# KMeans evaluation
print("\n✓ Evaluating KMeans:")
kmeans_sil = silhouette_score(X_scaled, kmeans_labels)
kmeans_db = davies_bouldin_score(X_scaled, kmeans_labels)
kmeans_ch = calinski_harabasz_score(X_scaled, kmeans_labels)
kmeans_ari = adjusted_rand_score(y_true, kmeans_labels)
kmeans_nmi = normalized_mutual_info_score(y_true, kmeans_labels)

print(f"  Silhouette Score:     {kmeans_sil:.4f}")
print(f"  Davies-Bouldin Index: {kmeans_db:.4f}")
print(f"  Calinski-Harabasz:    {kmeans_ch:.4f}")
print(f"  Adjusted Rand Index:  {kmeans_ari:.4f}")
print(f"  Normalized Mutual Info: {kmeans_nmi:.4f}")

results_table.append({
    'Algorithm': 'KMeans',
    'Clusters': optimal_k,
    'Silhouette': kmeans_sil,
    'Davies-Bouldin': kmeans_db,
    'Calinski-Harabasz': kmeans_ch,
    'ARI': kmeans_ari,
    'NMI': kmeans_nmi
})

# Agglomerative evaluation
print("\n✓ Evaluating Agglomerative Clustering (linkage={}):.".format(best_linkage))
agg_sil = silhouette_score(X_scaled, agg_labels)
agg_db = davies_bouldin_score(X_scaled, agg_labels)
agg_ch = calinski_harabasz_score(X_scaled, agg_labels)
agg_ari = adjusted_rand_score(y_true, agg_labels)
agg_nmi = normalized_mutual_info_score(y_true, agg_labels)

print(f"  Silhouette Score:     {agg_sil:.4f}")
print(f"  Davies-Bouldin Index: {agg_db:.4f}")
print(f"  Calinski-Harabasz:    {agg_ch:.4f}")
print(f"  Adjusted Rand Index:  {agg_ari:.4f}")
print(f"  Normalized Mutual Info: {agg_nmi:.4f}")

results_table.append({
    'Algorithm': f'Agglomerative ({best_linkage})',
    'Clusters': optimal_k,
    'Silhouette': agg_sil,
    'Davies-Bouldin': agg_db,
    'Calinski-Harabasz': agg_ch,
    'ARI': agg_ari,
    'NMI': agg_nmi
})

# DBSCAN evaluation
if n_clusters_dbscan > 0:
    print(f"\n✓ Evaluating DBSCAN (eps={best_dbscan[0]}, min_samples={best_dbscan[1]}):")
    
    # For DBSCAN, exclude outliers for metrics
    mask = dbscan_labels != -1
    X_no_outliers = X_scaled[mask]
    labels_no_outliers = dbscan_labels[mask]
    y_no_outliers = y_true[mask]
    
    if len(np.unique(labels_no_outliers)) > 1:
        dbscan_sil = silhouette_score(X_no_outliers, labels_no_outliers)
        dbscan_db = davies_bouldin_score(X_no_outliers, labels_no_outliers)
        dbscan_ch = calinski_harabasz_score(X_no_outliers, labels_no_outliers)
        dbscan_ari = adjusted_rand_score(y_no_outliers, labels_no_outliers)
        dbscan_nmi = normalized_mutual_info_score(y_no_outliers, labels_no_outliers)
        
        print(f"  Silhouette Score:     {dbscan_sil:.4f}")
        print(f"  Davies-Bouldin Index: {dbscan_db:.4f}")
        print(f"  Calinski-Harabasz:    {dbscan_ch:.4f}")
        print(f"  Adjusted Rand Index:  {dbscan_ari:.4f}")
        print(f"  Normalized Mutual Info: {dbscan_nmi:.4f}")
        print(f"  Outliers: {n_outliers_dbscan} ({n_outliers_dbscan/len(X_scaled)*100:.2f}%)")
        
        results_table.append({
            'Algorithm': 'DBSCAN',
            'Clusters': n_clusters_dbscan,
            'Silhouette': dbscan_sil,
            'Davies-Bouldin': dbscan_db,
            'Calinski-Harabasz': dbscan_ch,
            'ARI': dbscan_ari,
            'NMI': dbscan_nmi
        })

# ============================================================================
# STEP 5: RESULTS COMPARISON TABLE
# ============================================================================

print("\n" + "="*80)
print("CLUSTERING RESULTS COMPARISON TABLE")
print("="*80)

results_df = pd.DataFrame(results_table)
print(results_df.round(4).to_string(index=False))

# ============================================================================
# STEP 6: CLUSTER ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("STEP 6: CLUSTER ANALYSIS")
print("="*80)

print("\n✓ KMeans Cluster Sizes:")
kmeans_counts = pd.Series(kmeans_labels).value_counts().sort_index()
for cluster_id, count in kmeans_counts.items():
    pct = count / len(kmeans_labels) * 100
    print(f"  Cluster {cluster_id}: {count:4d} samples ({pct:.1f}%)")

print("\n✓ Agglomerative Cluster Sizes:")
agg_counts = pd.Series(agg_labels).value_counts().sort_index()
for cluster_id, count in agg_counts.items():
    pct = count / len(agg_labels) * 100
    print(f"  Cluster {cluster_id}: {count:4d} samples ({pct:.1f}%)")

if n_clusters_dbscan > 0:
    print("\n✓ DBSCAN Cluster Sizes:")
    dbscan_counts = pd.Series(dbscan_labels).value_counts().sort_index()
    for cluster_id, count in dbscan_counts.items():
        if cluster_id == -1:
            print(f"  Outliers: {count:4d} samples ({count/len(dbscan_labels)*100:.1f}%)")
        else:
            print(f"  Cluster {cluster_id}: {count:4d} samples ({count/len(dbscan_labels)*100:.1f}%)")

# ============================================================================
# STEP 7: PCA VISUALIZATION
# ============================================================================

print("\n" + "="*80)
print("STEP 7: DIMENSIONALITY REDUCTION (PCA) FOR VISUALIZATION")
print("="*80)

print("\n✓ Applying PCA (2 components)...")
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

print(f"  Explained variance ratio: {pca.explained_variance_ratio_}")
print(f"  Total variance explained: {pca.explained_variance_ratio_.sum():.4f}")

# ============================================================================
# GRAPHICS: 1. ELBOW METHOD & SILHOUETTE
# ============================================================================

print("\n" + "="*80)
print("GRAPHICS GENERATION")
print("="*80)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Elbow Method
axes[0].plot(k_range, inertias, 'bo-', linewidth=2, markersize=8)
axes[0].axvline(x=optimal_k, color='r', linestyle='--', linewidth=2, label=f'Optimal k={optimal_k}')
axes[0].set_xlabel('Number of Clusters (k)', fontsize=12)
axes[0].set_ylabel('Inertia', fontsize=12)
axes[0].set_title('Elbow Method for Optimal k', fontsize=14, fontweight='bold')
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# Silhouette Scores
axes[1].plot(k_range, silhouette_scores, 'go-', linewidth=2, markersize=8)
axes[1].axvline(x=optimal_k, color='r', linestyle='--', linewidth=2, label=f'Optimal k={optimal_k}')
axes[1].axhline(y=max(silhouette_scores), color='orange', linestyle=':', alpha=0.7)
axes[1].set_xlabel('Number of Clusters (k)', fontsize=12)
axes[1].set_ylabel('Silhouette Score', fontsize=12)
axes[1].set_title('Silhouette Analysis for KMeans', fontsize=14, fontweight='bold')
axes[1].grid(True, alpha=0.3)
axes[1].legend()

plt.tight_layout()
plt.savefig('01_elbow_silhouette.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: 01_elbow_silhouette.png")
plt.close()

# ============================================================================
# GRAPHICS: 2. KMEANS PCA VISUALIZATION
# ============================================================================

fig, ax = plt.subplots(figsize=(10, 8))

scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=kmeans_labels, cmap='viridis', 
                     s=100, alpha=0.6, edgecolors='black', linewidth=0.5)

# Plot cluster centers
centers_pca = pca.transform(kmeans.cluster_centers_)
ax.scatter(centers_pca[:, 0], centers_pca[:, 1], c='red', marker='X', s=500, 
          edgecolors='black', linewidth=2, label='Centroids', zorder=5)

ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=12)
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=12)
ax.set_title(f'KMeans Clustering (k={optimal_k}) - PCA Visualization', 
            fontsize=14, fontweight='bold')
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Cluster', fontsize=12)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('02_kmeans_pca.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 02_kmeans_pca.png")
plt.close()

# ============================================================================
# GRAPHICS: 3. AGGLOMERATIVE PCA VISUALIZATION
# ============================================================================

fig, ax = plt.subplots(figsize=(10, 8))

scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=agg_labels, cmap='plasma', 
                     s=100, alpha=0.6, edgecolors='black', linewidth=0.5)

ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=12)
ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=12)
ax.set_title(f'Agglomerative Clustering (linkage={best_linkage}) - PCA Visualization', 
            fontsize=14, fontweight='bold')
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Cluster', fontsize=12)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('03_agglomerative_pca.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 03_agglomerative_pca.png")
plt.close()

# ============================================================================
# GRAPHICS: 4. DBSCAN PCA VISUALIZATION
# ============================================================================

if n_clusters_dbscan > 0:
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Color outliers differently
    colors = dbscan_labels.copy().astype(float)
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=colors, cmap='cool', 
                        s=100, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    # Highlight outliers
    outlier_mask = dbscan_labels == -1
    ax.scatter(X_pca[outlier_mask, 0], X_pca[outlier_mask, 1], 
              marker='x', s=200, c='red', linewidth=2, label='Outliers', zorder=5)
    
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=12)
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=12)
    ax.set_title(f'DBSCAN Clustering (eps={best_dbscan[0]}) - PCA Visualization', 
                fontsize=14, fontweight='bold')
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Cluster', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('04_dbscan_pca.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: 04_dbscan_pca.png")
    plt.close()

# ============================================================================
# GRAPHICS: 5. CLUSTER SIZES HISTOGRAM
# ============================================================================

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# KMeans
kmeans_sizes = pd.Series(kmeans_labels).value_counts().sort_index()
axes[0].bar(kmeans_sizes.index, kmeans_sizes.values, color='steelblue', edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Cluster', fontsize=12)
axes[0].set_ylabel('Number of Samples', fontsize=12)
axes[0].set_title('KMeans - Cluster Sizes', fontsize=13, fontweight='bold')
axes[0].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(kmeans_sizes.values):
    axes[0].text(kmeans_sizes.index[i], v + 10, str(v), ha='center', fontweight='bold')

# Agglomerative
agg_sizes = pd.Series(agg_labels).value_counts().sort_index()
axes[1].bar(agg_sizes.index, agg_sizes.values, color='coral', edgecolor='black', alpha=0.7)
axes[1].set_xlabel('Cluster', fontsize=12)
axes[1].set_ylabel('Number of Samples', fontsize=12)
axes[1].set_title(f'Agglomerative ({best_linkage}) - Cluster Sizes', fontsize=13, fontweight='bold')
axes[1].grid(True, alpha=0.3, axis='y')
for i, v in enumerate(agg_sizes.values):
    axes[1].text(agg_sizes.index[i], v + 10, str(v), ha='center', fontweight='bold')

# DBSCAN
if n_clusters_dbscan > 0:
    dbscan_sizes = pd.Series(dbscan_labels).value_counts().sort_index()
    colors_bar = ['red' if x == -1 else 'lightgreen' for x in dbscan_sizes.index]
    axes[2].bar(range(len(dbscan_sizes)), dbscan_sizes.values, color=colors_bar, 
               edgecolor='black', alpha=0.7)
    axes[2].set_xlabel('Cluster', fontsize=12)
    axes[2].set_ylabel('Number of Samples', fontsize=12)
    axes[2].set_title('DBSCAN - Cluster & Outlier Sizes', fontsize=13, fontweight='bold')
    axes[2].set_xticks(range(len(dbscan_sizes)))
    axes[2].set_xticklabels([f'Out' if x == -1 else f'{x}' for x in dbscan_sizes.index])
    axes[2].grid(True, alpha=0.3, axis='y')
    for i, v in enumerate(dbscan_sizes.values):
        axes[2].text(i, v + 10, str(v), ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('05_cluster_sizes.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 05_cluster_sizes.png")
plt.close()

# ============================================================================
# GRAPHICS: 6. METRICS COMPARISON
# ============================================================================

fig, axes = plt.subplots(2, 3, figsize=(16, 10))

results_df_display = pd.DataFrame(results_table)
algorithms = results_df_display['Algorithm'].tolist()

metrics_data = {
    'Silhouette': results_df_display['Silhouette'].tolist(),
    'Davies-Bouldin': results_df_display['Davies-Bouldin'].tolist(),
    'Calinski-Harabasz': results_df_display['Calinski-Harabasz'].tolist(),
    'ARI': results_df_display['ARI'].tolist(),
    'NMI': results_df_display['NMI'].tolist()
}

colors_alg = ['steelblue', 'coral', 'lightgreen'][:len(algorithms)]

# Silhouette
axes[0, 0].bar(algorithms, metrics_data['Silhouette'], color=colors_alg, 
              edgecolor='black', alpha=0.7)
axes[0, 0].set_ylabel('Score', fontsize=11)
axes[0, 0].set_title('Silhouette Score\n(Higher is Better)', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3, axis='y')
axes[0, 0].tick_params(axis='x', rotation=15)

# Davies-Bouldin
axes[0, 1].bar(algorithms, metrics_data['Davies-Bouldin'], color=colors_alg, 
              edgecolor='black', alpha=0.7)
axes[0, 1].set_ylabel('Index', fontsize=11)
axes[0, 1].set_title('Davies-Bouldin Index\n(Lower is Better)', fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3, axis='y')
axes[0, 1].tick_params(axis='x', rotation=15)

# Calinski-Harabasz
axes[0, 2].bar(algorithms, metrics_data['Calinski-Harabasz'], color=colors_alg, 
              edgecolor='black', alpha=0.7)
axes[0, 2].set_ylabel('Index', fontsize=11)
axes[0, 2].set_title('Calinski-Harabasz Index\n(Higher is Better)', fontsize=12, fontweight='bold')
axes[0, 2].grid(True, alpha=0.3, axis='y')
axes[0, 2].tick_params(axis='x', rotation=15)

# ARI
axes[1, 0].bar(algorithms, metrics_data['ARI'], color=colors_alg, 
              edgecolor='black', alpha=0.7)
axes[1, 0].set_ylabel('Score', fontsize=11)
axes[1, 0].set_title('Adjusted Rand Index (ARI)\n(Higher = Better Agreement)', 
                     fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3, axis='y')
axes[1, 0].tick_params(axis='x', rotation=15)

# NMI
axes[1, 1].bar(algorithms, metrics_data['NMI'], color=colors_alg, 
              edgecolor='black', alpha=0.7)
axes[1, 1].set_ylabel('Score', fontsize=11)
axes[1, 1].set_title('Normalized Mutual Information (NMI)\n(Higher = Better Agreement)', 
                     fontsize=12, fontweight='bold')
axes[1, 1].grid(True, alpha=0.3, axis='y')
axes[1, 1].tick_params(axis='x', rotation=15)

# Clusters count
axes[1, 2].bar(algorithms, results_df_display['Clusters'].tolist(), color=colors_alg, 
              edgecolor='black', alpha=0.7)
axes[1, 2].set_ylabel('Number of Clusters', fontsize=11)
axes[1, 2].set_title('Number of Clusters Found', fontsize=12, fontweight='bold')
axes[1, 2].grid(True, alpha=0.3, axis='y')
axes[1, 2].tick_params(axis='x', rotation=15)

plt.tight_layout()
plt.savefig('06_metrics_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 06_metrics_comparison.png")
plt.close()

# ============================================================================
# GRAPHICS: 7. SILHOUETTE PLOTS
# ============================================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# KMeans Silhouette
silhouette_vals_km = silhouette_samples(X_scaled, kmeans_labels)
y_lower = 10
colors_km = plt.cm.viridis(np.linspace(0, 1, optimal_k))

for i in range(optimal_k):
    cluster_silhouette_vals = silhouette_vals_km[kmeans_labels == i]
    cluster_silhouette_vals.sort()
    
    size_cluster_i = cluster_silhouette_vals.shape[0]
    y_upper = y_lower + size_cluster_i
    
    axes[0].fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_silhouette_vals,
                          facecolor=colors_km[i], edgecolor=colors_km[i], alpha=0.7)
    y_lower = y_upper + 10

axes[0].axvline(x=kmeans_sil, color="red", linestyle="--", linewidth=2, 
               label=f'Average: {kmeans_sil:.3f}')
axes[0].set_xlabel('Silhouette Coefficient', fontsize=11)
axes[0].set_ylabel('Cluster', fontsize=11)
axes[0].set_title('KMeans - Silhouette Plot', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(True, alpha=0.3, axis='x')

# Agglomerative Silhouette
silhouette_vals_agg = silhouette_samples(X_scaled, agg_labels)
y_lower = 10
colors_agg = plt.cm.plasma(np.linspace(0, 1, optimal_k))

for i in range(optimal_k):
    cluster_silhouette_vals = silhouette_vals_agg[agg_labels == i]
    cluster_silhouette_vals.sort()
    
    size_cluster_i = cluster_silhouette_vals.shape[0]
    y_upper = y_lower + size_cluster_i
    
    axes[1].fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_silhouette_vals,
                          facecolor=colors_agg[i], edgecolor=colors_agg[i], alpha=0.7)
    y_lower = y_upper + 10

axes[1].axvline(x=agg_sil, color="red", linestyle="--", linewidth=2, 
               label=f'Average: {agg_sil:.3f}')
axes[1].set_xlabel('Silhouette Coefficient', fontsize=11)
axes[1].set_ylabel('Cluster', fontsize=11)
axes[1].set_title(f'Agglomerative ({best_linkage}) - Silhouette Plot', 
                 fontsize=12, fontweight='bold')
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis='x')

# DBSCAN Silhouette (if applicable)
if n_clusters_dbscan > 0:
    mask = dbscan_labels != -1
    silhouette_vals_dbscan = silhouette_samples(X_scaled[mask], dbscan_labels[mask])
    y_lower = 10
    colors_dbscan = plt.cm.cool(np.linspace(0, 1, n_clusters_dbscan))
    
    for i in range(n_clusters_dbscan):
        cluster_silhouette_vals = silhouette_vals_dbscan[dbscan_labels[mask] == i]
        cluster_silhouette_vals.sort()
        
        size_cluster_i = cluster_silhouette_vals.shape[0]
        y_upper = y_lower + size_cluster_i
        
        axes[2].fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_silhouette_vals,
                              facecolor=colors_dbscan[i], edgecolor=colors_dbscan[i], alpha=0.7)
        y_lower = y_upper + 10
    
    axes[2].axvline(x=dbscan_sil, color="red", linestyle="--", linewidth=2, 
                   label=f'Average: {dbscan_sil:.3f}')
    axes[2].set_xlabel('Silhouette Coefficient', fontsize=11)
    axes[2].set_ylabel('Cluster', fontsize=11)
    axes[2].set_title('DBSCAN - Silhouette Plot', fontsize=12, fontweight='bold')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('07_silhouette_plots.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 07_silhouette_plots.png")
plt.close()

# ============================================================================
# GRAPHICS: 8. FEATURE DISTRIBUTION BY CLUSTERS
# ============================================================================

fig, axes = plt.subplots(2, 4, figsize=(18, 10))
axes = axes.flatten()

X_plot = X_scaled.copy()
X_plot['KMeans'] = kmeans_labels

features_to_plot = X_plot.columns[:-1]

for idx, feature in enumerate(features_to_plot):
    data_to_plot = [X_plot[X_plot['KMeans'] == i][feature].values for i in range(optimal_k)]
    
    axes[idx].boxplot(data_to_plot, labels=[f'C{i}' for i in range(optimal_k)])
    axes[idx].set_ylabel('Scaled Value', fontsize=10)
    axes[idx].set_title(f'{feature} - Distribution by Cluster', fontsize=11, fontweight='bold')
    axes[idx].grid(True, alpha=0.3, axis='y')

# Hide last unused subplot
axes[-1].axis('off')

plt.tight_layout()
plt.savefig('08_feature_distribution.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 08_feature_distribution.png")
plt.close()

# ============================================================================
# GRAPHICS: 9. K-DISTANCE GRAPH FOR DBSCAN
# ============================================================================

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(distances, linewidth=1.5, color='steelblue')
ax.axhline(y=best_dbscan[0], color='red', linestyle='--', linewidth=2, 
          label=f'Selected eps={best_dbscan[0]}')
ax.set_xlabel('Data Points (sorted)', fontsize=12)
ax.set_ylabel('4th Nearest Neighbor Distance', fontsize=12)
ax.set_title('K-Distance Graph for DBSCAN (k=4)', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('09_k_distance_graph.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 09_k_distance_graph.png")
plt.close()

# ============================================================================
# GRAPHICS: 10. CLUSTERING VS TRUE LABELS
# ============================================================================

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# KMeans vs True
scatter1 = axes[0].scatter(X_pca[:, 0], X_pca[:, 1], c=kmeans_labels, cmap='viridis', 
                          s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
axes[0].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=11)
axes[0].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=11)
axes[0].set_title('KMeans Clustering', fontsize=12, fontweight='bold')
plt.colorbar(scatter1, ax=axes[0], label='Cluster')
axes[0].grid(True, alpha=0.3)

# Agglomerative vs True
scatter2 = axes[1].scatter(X_pca[:, 0], X_pca[:, 1], c=agg_labels, cmap='plasma', 
                          s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
axes[1].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=11)
axes[1].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=11)
axes[1].set_title(f'Agglomerative ({best_linkage})', fontsize=12, fontweight='bold')
plt.colorbar(scatter2, ax=axes[1], label='Cluster')
axes[1].grid(True, alpha=0.3)

# True Labels
scatter3 = axes[2].scatter(X_pca[:, 0], X_pca[:, 1], c=y_true, cmap='RdYlGn', 
                          s=80, alpha=0.6, edgecolors='black', linewidth=0.5)
axes[2].set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%})', fontsize=11)
axes[2].set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', fontsize=11)
axes[2].set_title('True Labels (Charges Level)', fontsize=12, fontweight='bold')
plt.colorbar(scatter3, ax=axes[2], label='Label')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('10_clustering_vs_true.png', dpi=300, bbox_inches='tight')
print("✓ Saved: 10_clustering_vs_true.png")
plt.close()
