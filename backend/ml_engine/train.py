import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), 'weights')
os.makedirs(WEIGHTS_DIR, exist_ok=True)

def train_model():
    print("Loading master dataset...")
    data_path = os.path.join(DATA_DIR, 'master_dataset.csv')
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}. Please run dataset_builder.py first.")
        return
        
    df = pd.read_csv(data_path)
    
    # Feature columns based on our dataset_builder
    feature_cols = ['studytime', 'failures', 'health', 'absences', 'current_pct', 'recent_5_classes_present']
    X = df[feature_cols]
    y = df['is_at_risk']
    
    print("Splitting data into train/test sets (10% test split = ~11,000 records)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42, stratify=y)
    
    print("Fine-tuning Random Forest Classifier via GridSearchCV...")
    from sklearn.model_selection import GridSearchCV
    
    # We define a parameter grid for fine tuning
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5]
    }
    
    rf_base = RandomForestClassifier(random_state=42, class_weight='balanced')
    grid_search = GridSearchCV(estimator=rf_base, param_grid=param_grid, cv=3, n_jobs=-1, verbose=1)
    
    grid_search.fit(X_train, y_train)
    
    print(f"Best hyperparameters found: {grid_search.best_params_}")
    model = grid_search.best_estimator_
    
    print("Evaluating fine-tuned model...")
    y_pred = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))
    
    model_path = os.path.join(WEIGHTS_DIR, 'absenteeism_rf_model.joblib')
    joblib.dump(model, model_path)
    print(f"Model successfully saved to: {model_path}")

if __name__ == "__main__":
    train_model()
