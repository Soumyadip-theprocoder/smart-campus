import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.svm import LinearSVR
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os
import time

def train_grade_forecaster():
    print("Loading augmented organic dataset (1,000,000 records)...")
    df = pd.read_csv('data/augmented_regression_dataset.csv')
    
    X = df[['marks_10th', 'marks_12th', 'attendance_pct']]
    y = df['final_cgpa']
    
    # 80/20 Split (200,000 test records, > 10,000 required)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Training set: {X_train.shape[0]} records")
    print(f"Test set: {X_test.shape[0]} records")
    
    # Fine-Tuning Models on a subset to save time (50,000 records)
    print("Fine-tuning models on a 50,000 record subset...")
    X_tune, _, y_tune, _ = train_test_split(X_train, y_train, train_size=50000, random_state=42)
    
    models = {
        'LinearRegression': {
            'model': LinearRegression(),
            'params': {}
        },
        'LinearSVR': {
            'model': LinearSVR(random_state=42, max_iter=2000),
            'params': {
                'C': [0.1, 1, 10]
            }
        },
        'RandomForestRegressor': {
            'model': RandomForestRegressor(random_state=42, n_jobs=-1),
            'params': {
                'n_estimators': [20, 50],
                'max_depth': [5, 10]
            }
        }
    }
    
    best_model_name = ""
    best_model = None
    best_r2 = -float('inf')
    
    print("\n--- Model Evaluation & Hyperparameter Tuning ---")
    for name, config in models.items():
        print(f"Tuning {name}...")
        start = time.time()
        clf = GridSearchCV(config['model'], config['params'], cv=3, scoring='r2', n_jobs=-1)
        clf.fit(X_tune, y_tune)
        elapsed = time.time() - start
        
        print(f"Best Params for {name}: {clf.best_params_} (Time: {elapsed:.2f}s)")
        print(f"Best Subset CV R2: {clf.best_score_:.4f}")
        
        if clf.best_score_ > best_r2:
            best_r2 = clf.best_score_
            best_model_name = name
            best_model = clf.best_estimator_
            
    print(f"\nWinning Model: {best_model_name}")
    print("Training winning model on full 800,000 record training set...")
    start = time.time()
    best_model.fit(X_train, y_train)
    elapsed = time.time() - start
    print(f"Full training complete in {elapsed:.2f}s")
    
    # Evaluate on the 200,000 record test set
    print(f"\n--- Testing on {X_test.shape[0]} unseen records ---")
    y_pred = best_model.predict(X_test)
    
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Mean Squared Error (MSE): {mse:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.4f}")
    print(f"R-Squared (R2 Score): {r2:.4f}")
    print(f"Accuracy/Precision equivalent (R2): {r2*100:.2f}% variance explained")
    
    # Save the model
    os.makedirs('models', exist_ok=True)
    model_path = 'models/cgpa_forecaster.joblib'
    joblib.dump(best_model, model_path)
    print(f"\nModel serialized and saved to {model_path}")

if __name__ == "__main__":
    train_grade_forecaster()
