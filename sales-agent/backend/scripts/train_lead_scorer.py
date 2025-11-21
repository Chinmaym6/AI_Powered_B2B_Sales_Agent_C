import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle
from pathlib import Path
import os

def create_bootstrap_dataset():
    """
    Create initial training dataset from sample data
    """
    print("📊 Creating bootstrap dataset...")
    
    # Sample data
    np.random.seed(42)
    n_samples = 200
    
    data = {
        'keyword_match_score': np.random.rand(n_samples),
        'company_size_log': np.random.rand(n_samples) * 10,
        'industry_relevance': np.random.choice([0, 1], n_samples),
        'contact_completeness': np.random.rand(n_samples),
        'email_available': np.random.choice([0, 1], n_samples),
        'linkedin_available': np.random.choice([0, 1], n_samples),
        'has_https': np.random.choice([0, 1], n_samples),
        'description_length_log': np.random.rand(n_samples) * 8,
        'has_funding_mention': np.random.choice([0, 1], n_samples),
        'tech_stack_count': np.random.randint(0, 8, n_samples),
        'pain_point_match': np.random.rand(n_samples),
        
        # Label: 1 = good lead, 0 = bad lead
        'is_good_lead': np.random.choice([0, 1], n_samples, p=[0.3, 0.7])
    }
    
    return pd.DataFrame(data)

def train_model(df: pd.DataFrame):
    """Train XGBoost model"""
    
    print("🧠 Training XGBoost model...")
    
    # Split features and target
    X = df.drop('is_good_lead', axis=1)
    y = df['is_good_lead']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost
    model = xgb.XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        objective='binary:logistic',
        eval_metric='logloss',
        random_state=42
    )
    
    model.fit(
        X_train_scaled, 
        y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred)
    }
    
    print("\n📈 Model Performance:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.3f}")
    
    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    model.save_model(str(models_dir / "lead_scorer_v1.json"))
    
    # Save scaler
    with open(models_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    
    print(f"\n✅ Model saved to {models_dir / 'lead_scorer_v1.json'}")
    
    return model, metrics

if __name__ == "__main__":
    # Ensure we are in the backend directory or adjust paths
    # This script assumes it's run from backend/ or backend/scripts/
    
    # Change to backend directory if we are in scripts
    if Path.cwd().name == "scripts":
        os.chdir("..")
        
    print("🚀 Starting ML training pipeline...")
    
    # Create bootstrap dataset
    df = create_bootstrap_dataset()
    
    # Train model
    model, metrics = train_model(df)
    
    print("\n🎉 Training complete!")
