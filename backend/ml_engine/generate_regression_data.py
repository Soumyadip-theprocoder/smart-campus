import pandas as pd
import numpy as np
import os

def generate_data(num_records=1_000_000):
    print(f"Generating {num_records} synthetic records for Grade Forecasting...")
    np.random.seed(42)
    
    # 10th and 12th marks (normally distributed around 75, bounded 40-100)
    marks_10th = np.clip(np.random.normal(75, 12, num_records), 40, 100)
    marks_12th = np.clip(np.random.normal(70, 15, num_records), 40, 100)
    
    # Attendance % (highly correlated with passing, mostly 60-100)
    attendance_pct = np.clip(np.random.normal(80, 15, num_records), 0, 100)
    
    # Base CGPA depends heavily on historical marks
    base_cgpa = (marks_10th * 0.3 + marks_12th * 0.4) / 10.0
    
    # Attendance modifier: poor attendance drops CGPA, good attendance boosts it
    # Attendance of 75 is neutral. Every 10% above 75 adds 0.5 CGPA, every 10% below drops 0.7 CGPA.
    attendance_modifier = np.where(
        attendance_pct >= 75,
        (attendance_pct - 75) * 0.05,
        (attendance_pct - 75) * 0.07
    )
    
    # Add some random noise
    noise = np.random.normal(0, 0.5, num_records)
    
    final_cgpa = np.clip(base_cgpa + attendance_modifier + noise, 0.0, 10.0)
    
    df = pd.DataFrame({
        'marks_10th': np.round(marks_10th, 2),
        'marks_12th': np.round(marks_12th, 2),
        'attendance_pct': np.round(attendance_pct, 2),
        'final_cgpa': np.round(final_cgpa, 2)
    })
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/regression_dataset.csv', index=False)
    print("Dataset generated and saved to data/regression_dataset.csv")

if __name__ == "__main__":
    generate_data()
