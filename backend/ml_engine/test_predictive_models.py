import pytest
import itertools
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from predictive_models import _predict_from_features

# 13.1-UAT.md Dimensions (504 Permutations = 7 x 6 x 4 x 3)

# Dimension A: Current Historical Ratios (7 states)
ratios = [0.0, 25.0, 50.0, 74.0, 75.0, 76.0, 100.0]

# Dimension B: Sequence Trend Profiles (6 states)
# We map these to `recent_5_classes_present`
trends = [
    5, # Improving (Recent mostly present)
    1, # Degrading (Recent mostly absent)
    3, # Stable_Alternating
    2, # Random_Noise
    5, # All_Present_Streak
    0  # All_Absent_Streak
]

# Dimension C: Data Sparsity & Missing Values (4 states)
# We map these to `absences`
sparsities = [
    0,   # Zero_History (Day 1)
    1,   # Single_Record
    20,  # Intermittent_Nulls (missing gaps, derived high absences)
    90   # Dense_History (lots of records)
]

# Dimension D: Contextual Factors (3 states)
# We map these to `studytime` and `failures` to simulate different subjects
contexts = [
    {'studytime': 2, 'failures': 0, 'health': 3}, # Theory
    {'studytime': 4, 'failures': 0, 'health': 5}, # Lab (High engagement)
    {'studytime': 1, 'failures': 2, 'health': 1}  # Elective (Low engagement)
]

# Generate the 504 combinations
all_combinations = list(itertools.product(ratios, trends, sparsities, contexts))

@pytest.mark.parametrize("ratio, trend, sparsity, context", all_combinations)
def test_ml_boundaries_504_permutations(ratio, trend, sparsity, context):
    """
    AC-1, AC-2, AC-3: Asserts the 504 boundaries of the predictive model.
    """
    features = {
        'studytime': context['studytime'],
        'failures': context['failures'],
        'health': context['health'],
        'absences': sparsity,
        'current_pct': ratio,
        'recent_5_classes_present': trend
    }
    
    # AC-1: Does not crash, handles all sparse and boundary data
    result = _predict_from_features(features)
    
    # AC-2: Validates schema return format
    assert 'current_pct' in result
    assert 'risk_probability' in result
    assert 'is_at_risk' in result
    assert isinstance(result['is_at_risk'], bool)
    
    # AC-3: Boundary Integrity - if probability > 50% or pct < 75%, MUST be flagged as at risk
    # Our internal logic overrides ML if pct < 75.
    if ratio < 75.0:
        assert result['is_at_risk'] is True
        
    if result['risk_probability'] > 0.5:
        assert result['is_at_risk'] is True
