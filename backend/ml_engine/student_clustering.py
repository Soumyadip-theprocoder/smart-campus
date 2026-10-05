import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, MiniBatchKMeans, DBSCAN, Birch, MeanShift
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import joblib
import os
import time
import warnings

warnings.filterwarnings('ignore')

def train_student_clustering():
    print("Loading augmented organic dataset (1,000,000 records) for Clustering...")
    df = pd.read_csv('data/augmented_regression_dataset.csv')
    
    # We cluster students based on their effort (attendance) vs outcomes (marks/CGPA)
    # to find behavioral profiles like "High Effort/Low Output"
    features = ['marks_10th', 'marks_12th', 'attendance_pct', 'final_cgpa']
    X = df[features]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Clustering 1,000,000 rows with DBSCAN or MeanShift takes massive RAM/Time (O(N^2)).
    # We evaluate on a 20,000 record subset for the "Algorithmic Showdown".
    print("\n--- Algorithmic Showdown (Evaluating on 20,000 record subset) ---")
    np.random.seed(42)
    subset_indices = np.random.choice(X_scaled.shape[0], 20000, replace=False)
    X_subset = X_scaled[subset_indices]
    
    models = {
        'MiniBatchKMeans': MiniBatchKMeans(n_clusters=4, random_state=42, batch_size=1024),
        'GaussianMixture': GaussianMixture(n_components=4, random_state=42),
        'BIRCH': Birch(n_clusters=4, threshold=0.5),
        'DBSCAN': DBSCAN(eps=0.5, min_samples=10),
        # MeanShift is omitted as it hangs even on 20k rows (highly unoptimized for density)
    }
    
    best_model_name = ""
    best_score = -1
    best_model_instance = None
    
    for name, model in models.items():
        print(f"Evaluating {name}...")
        start = time.time()
        
        if name == 'GaussianMixture':
            labels = model.fit_predict(X_subset)
        else:
            labels = model.fit_predict(X_subset)
            
        elapsed = time.time() - start
        
        # If DBSCAN finds only 1 cluster or too much noise, silhouette throws an error
        unique_labels = np.unique(labels)
        if len(unique_labels) > 1:
            score = silhouette_score(X_subset, labels)
            ch_score = calinski_harabasz_score(X_subset, labels)
            print(f"  -> Silhouette Score: {score:.4f} (Higher is better)")
            print(f"  -> Calinski-Harabasz: {ch_score:.1f}")
            print(f"  -> Time: {elapsed:.2f}s")
            
            if score > best_score and name != 'DBSCAN': # DBSCAN doesn't scale to 1M easily for prediction
                best_score = score
                best_model_name = name
                best_model_instance = models[name]
        else:
            print(f"  -> Failed to find distinct clusters.")
            
    print(f"\nWinning Model: {best_model_name} (Silhouette: {best_score:.4f})")
    
    # 2. Optimal Cluster Selection using Elbow/Silhouette on the winner
    print(f"\n--- Finding Optimal Cluster Count (k) for {best_model_name} ---")
    best_k = 4
    if best_model_name == 'MiniBatchKMeans':
        best_k_score = -1
        for k in [3, 4, 5]:
            km = MiniBatchKMeans(n_clusters=k, random_state=42, batch_size=1024)
            labels = km.fit_predict(X_subset)
            score = silhouette_score(X_subset, labels)
            print(f"k={k} Silhouette Score: {score:.4f}")
            if score > best_k_score:
                best_k_score = score
                best_k = k
        print(f"Optimal clusters selected: {best_k}")
        final_model = MiniBatchKMeans(n_clusters=best_k, random_state=42, batch_size=2048)
    else:
        final_model = GaussianMixture(n_components=4, random_state=42)
        
    print("\n--- Training Final Model on Full 1,000,000 Records ---")
    start = time.time()
    final_model.fit(X_scaled)
    elapsed = time.time() - start
    print(f"Full training complete in {elapsed:.2f}s")
    
    # Serialize the scaler and the model
    os.makedirs('models', exist_ok=True)
    joblib.dump(scaler, 'models/cluster_scaler.joblib')
    joblib.dump(final_model, 'models/student_clustering.joblib')
    print("Model and Scaler serialized to models/")

if __name__ == "__main__":
    train_student_clustering()
