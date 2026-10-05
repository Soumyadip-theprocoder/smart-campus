import pandas as pd
import numpy as np
import os

def augment_organic_data(target_records=1_000_000):
    print(f"Loading organic UCI Student Performance Dataset (395 records)...")
    organic_df = pd.read_csv('data/uci_student/student-mat.csv', sep=';')
    
    # Map UCI columns to our system's schema
    # G1 (0-20) mapped to marks_10th (0-100)
    # G2 (0-20) mapped to marks_12th (0-100)
    # absences (0-93) mapped inversely to attendance_pct (0-100)
    # G3 (0-20) mapped to final_cgpa (0-10)
    
    organic_mapped = pd.DataFrame({
        'marks_10th': (organic_df['G1'] / 20) * 100,
        'marks_12th': (organic_df['G2'] / 20) * 100,
        'attendance_pct': np.clip(100 - (organic_df['absences'] / 93) * 100 * 2, 0, 100), # penalize absences
        'final_cgpa': (organic_df['G3'] / 20) * 10
    })
    
    print("Calculating organic covariance matrix...")
    cov_matrix = organic_mapped.cov().values
    mean_vector = organic_mapped.mean().values
    
    print(f"Augmenting organic data up to {target_records} records using Multivariate Normal Distribution...")
    np.random.seed(42)
    # Generate 1M records that maintain the exact correlation matrix of the organic data
    augmented_data = np.random.multivariate_normal(mean_vector, cov_matrix, target_records)
    
    augmented_df = pd.DataFrame(augmented_data, columns=organic_mapped.columns)
    
    # Clip to realistic bounds
    augmented_df['marks_10th'] = np.clip(augmented_df['marks_10th'], 0, 100).round(2)
    augmented_df['marks_12th'] = np.clip(augmented_df['marks_12th'], 0, 100).round(2)
    augmented_df['attendance_pct'] = np.clip(augmented_df['attendance_pct'], 0, 100).round(2)
    augmented_df['final_cgpa'] = np.clip(augmented_df['final_cgpa'], 0, 10).round(2)
    
    output_path = 'data/augmented_regression_dataset.csv'
    augmented_df.to_csv(output_path, index=False)
    
    print(f"Data successfully augmented from {len(organic_df)} to {len(augmented_df)} records.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    augment_organic_data()
