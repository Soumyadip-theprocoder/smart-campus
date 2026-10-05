import os
import joblib
import pandas as pd
from django.conf import settings
from apps.attendance.models import Attendance
import logging

logger = logging.getLogger(__name__)

# Cache models in memory
_cgpa_model = None
_cluster_model = None
_cluster_scaler = None

def load_models():
    global _cgpa_model, _cluster_model, _cluster_scaler
    models_dir = os.path.join(settings.BASE_DIR, 'ml_engine', 'models')
    
    if _cgpa_model is None:
        try:
            _cgpa_model = joblib.load(os.path.join(models_dir, 'cgpa_forecaster.joblib'))
        except Exception as e:
            logger.error(f"Failed to load cgpa_forecaster: {e}")
            
    if _cluster_model is None:
        try:
            _cluster_model = joblib.load(os.path.join(models_dir, 'student_clustering.joblib'))
            _cluster_scaler = joblib.load(os.path.join(models_dir, 'cluster_scaler.joblib'))
        except Exception as e:
            logger.error(f"Failed to load student clustering models: {e}")

def get_student_features(student):
    """Calculates ML features from student's database records."""
    total_classes = Attendance.objects.filter(student=student).count()
    if total_classes == 0:
        attendance_pct = 0.0 # Default if no records
    else:
        present_classes = Attendance.objects.filter(student=student, status=Attendance.Status.PRESENT).count()
        attendance_pct = (present_classes / total_classes) * 100.0
        
    marks_10th = float(student.marks_10th) if student.marks_10th else 75.0
    marks_12th = float(student.marks_12th) if student.marks_12th else 75.0
    
    # Calculate a proxy final cgpa based on previous semesters if available, else 0
    cgpas = list(student.cgpa_semesters.values())
    current_cgpa = sum(cgpas)/len(cgpas) if cgpas else 0.0
    
    return {
        'marks_10th': marks_10th,
        'marks_12th': marks_12th,
        'attendance_pct': attendance_pct,
        'final_cgpa': current_cgpa
    }

def predict_cgpa_forecast(student):
    load_models()
    if _cgpa_model is None:
        return None
        
    features = get_student_features(student)
    
    # Regression model expects: ['marks_10th', 'marks_12th', 'attendance_pct']
    X = pd.DataFrame([{
        'marks_10th': features['marks_10th'],
        'marks_12th': features['marks_12th'],
        'attendance_pct': features['attendance_pct']
    }])
    
    try:
        prediction = _cgpa_model.predict(X)[0]
        return round(float(prediction), 2)
    except Exception as e:
        logger.error(f"Error predicting CGPA: {e}")
        return None

def get_student_cluster(student):
    load_models()
    if _cluster_model is None or _cluster_scaler is None:
        return None
        
    features = get_student_features(student)
    
    # Clustering model expects: ['marks_10th', 'marks_12th', 'attendance_pct', 'final_cgpa']
    X = pd.DataFrame([{
        'marks_10th': features['marks_10th'],
        'marks_12th': features['marks_12th'],
        'attendance_pct': features['attendance_pct'],
        'final_cgpa': features['final_cgpa']
    }])
    
    try:
        X_scaled = _cluster_scaler.transform(X)
        cluster_id = _cluster_model.predict(X_scaled)[0]
        
        # We can map cluster IDs to descriptive names based on organic clustering analysis
        # For a 3-cluster MiniBatchKMeans, we arbitrarily assign names for now, 
        # but in production, we would analyze the centroids to name them definitively.
        names = {
            0: "High Effort / At Target",
            1: "Disengaged / At Risk",
            2: "Neutral / Coasting"
        }
        return {
            "cluster_id": int(cluster_id),
            "profile_name": names.get(int(cluster_id), "Unknown")
        }
    except Exception as e:
        logger.error(f"Error clustering student: {e}")
        return None

def predict_absenteeism_risk(student_id, subject_id):
    """
    Evaluates the risk of a student failing due to absenteeism.
    Re-implemented missing function for Phase 13.1 compatibility.
    """
    total = Attendance.objects.filter(student_id=student_id, subject_id=subject_id).count()
    if total == 0:
        return {"is_at_risk": False, "current_pct": 100.0, "risk_probability": 0.0}
        
    present = Attendance.objects.filter(
        student_id=student_id, 
        subject_id=subject_id, 
        status=Attendance.Status.PRESENT
    ).count()
    
    pct = round((present / total) * 100, 2)
    is_at_risk = pct < 75.0
    
    # Simple probability mapped to how far below 75% they are (1.0 = 0%, 0.0 = 75%)
    risk_prob = 0.0
    if is_at_risk:
        risk_prob = round((75.0 - pct) / 75.0, 2)
        
    return {
        "is_at_risk": is_at_risk,
        "current_pct": pct,
        "risk_probability": risk_prob
    }
