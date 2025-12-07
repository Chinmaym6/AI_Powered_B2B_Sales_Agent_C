"""
Train XGBoost Lead Scorer from Custom CSV Dataset
==================================================
This script trains the ML model using YOUR OWN dataset (CSV file).
It does NOT modify the existing model unless you specify --replace.

Usage:
    python scripts/train_from_csv.py --data data/my_leads.csv
    python scripts/train_from_csv.py --data data/my_leads.csv --output models/custom_model.json
    python scripts/train_from_csv.py --data data/my_leads.csv --replace  # Replace active model

Required CSV columns:
    - keyword_match_score (0-1)
    - company_size_log (float)
    - industry_relevance (0-1)
    - contact_completeness (0-1)
    - email_available (0 or 1)
    - linkedin_available (0 or 1)
    - has_https (0 or 1)
    - description_length_log (float)
    - has_funding_mention (0 or 1)
    - tech_stack_count (int)
    - pain_point_match (0-1)
    - is_good_lead (0 or 1) <- THE LABEL
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, classification_report
)
import pickle
from pathlib import Path
import argparse
import shutil
from datetime import datetime


# Required feature columns (must match lead_scorer.py)
REQUIRED_FEATURES = [
    "keyword_match_score",
    "company_size_log",
    "industry_relevance",
    "contact_completeness",
    "email_available",
    "linkedin_available",
    "has_https",
    "description_length_log",
    "has_funding_mention",
    "tech_stack_count",
    "pain_point_match"
]

LABEL_COLUMN = "is_good_lead"


def validate_csv(df: pd.DataFrame) -> bool:
    """Validate that CSV has all required columns"""
    
    missing_features = [f for f in REQUIRED_FEATURES if f not in df.columns]
    
    if missing_features:
        print(f"❌ Missing feature columns: {missing_features}")
        return False
    
    if LABEL_COLUMN not in df.columns:
        print(f"❌ Missing label column: {LABEL_COLUMN}")
        return False
    
    # Check for valid label values
    unique_labels = df[LABEL_COLUMN].unique()
    if not set(unique_labels).issubset({0, 1}):
        print(f"❌ Invalid label values: {unique_labels}. Must be 0 or 1.")
        return False
    
    # Check for both classes
    if len(unique_labels) < 2:
        print(f"❌ Only one class found ({unique_labels[0]}). Need both 0 and 1.")
        return False
    
    print(f"✅ CSV validation passed!")
    return True


def load_and_prepare_data(csv_path: str) -> pd.DataFrame:
    """Load CSV and prepare data"""
    
    print(f"\n📂 Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    
    if not validate_csv(df):
        raise ValueError("CSV validation failed. Please check your data.")
    
    # Keep only required columns
    columns_to_keep = REQUIRED_FEATURES + [LABEL_COLUMN]
    df = df[columns_to_keep]
    
    # Handle missing values
    df = df.fillna(0)
    
    print(f"\n📊 Data Summary:")
    print(f"   Total samples: {len(df)}")
    print(f"   Good leads (1): {df[LABEL_COLUMN].sum()} ({df[LABEL_COLUMN].mean():.1%})")
    print(f"   Bad leads (0): {(1 - df[LABEL_COLUMN]).sum()} ({1 - df[LABEL_COLUMN].mean():.1%})")
    
    return df


def train_model(df: pd.DataFrame):
    """Train XGBoost model"""
    
    print("\n" + "=" * 60)
    print("🧠 TRAINING XGBOOST MODEL")
    print("=" * 60)
    
    # Split features and target
    X = df[REQUIRED_FEATURES]
    y = df[LABEL_COLUMN]
    
    print(f"\n📊 Features ({len(REQUIRED_FEATURES)}):")
    for i, name in enumerate(REQUIRED_FEATURES, 1):
        print(f"   {i:2}. {name}")
    
    # Train-test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📈 Dataset split:")
    print(f"   Training: {len(X_train)} samples")
    print(f"   Testing: {len(X_test)} samples")
    print(f"   Good leads in training: {y_train.sum()} ({y_train.mean():.1%})")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost
    print("\n🔥 Training XGBoost with optimized parameters...")
    
    model = xgb.XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=150,
        objective='binary:logistic',
        eval_metric='logloss',
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        use_label_encoder=False
    )
    
    model.fit(
        X_train_scaled, 
        y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False
    )
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    print("\n📊 MODEL PERFORMANCE:")
    print("-" * 40)
    
    metrics = {
        'Accuracy': accuracy_score(y_test, y_pred),
        'Precision': precision_score(y_test, y_pred, zero_division=0),
        'Recall': recall_score(y_test, y_pred, zero_division=0),
        'F1 Score': f1_score(y_test, y_pred, zero_division=0),
        'AUC-ROC': roc_auc_score(y_test, y_pred_proba)
    }
    
    for metric, value in metrics.items():
        bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
        print(f"   {metric:12}: {value:.3f} [{bar}]")
    
    print("\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Bad Lead', 'Good Lead']))
    
    # Feature importance
    print("\n🎯 FEATURE IMPORTANCE (Top 5):")
    importance = dict(zip(REQUIRED_FEATURES, model.feature_importances_))
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(sorted_importance[:5], 1):
        bar = "█" * int(imp * 50)
        print(f"   {i}. {feat:25}: {imp:.3f} [{bar}]")
    
    return model, scaler, metrics


def save_model(model, scaler, metrics, output_path: str, replace: bool = False):
    """Save the trained model"""
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    output_file = Path(output_path)
    
    # Backup existing model if replacing
    if replace:
        active_model = models_dir / "lead_scorer_v1.json"
        if active_model.exists():
            backup_name = f"lead_scorer_v1_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy(active_model, models_dir / backup_name)
            print(f"\n💾 Backed up existing model to: {backup_name}")
        
        output_file = active_model
    
    # Save model
    model.save_model(str(output_file))
    print(f"✅ Model saved to: {output_file}")
    
    # Save scaler (same location as model)
    scaler_path = output_file.parent / f"{output_file.stem}_scaler.pkl"
    if replace:
        scaler_path = models_dir / "scaler.pkl"
    
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"✅ Scaler saved to: {scaler_path}")
    
    # Save metrics
    metrics_path = output_file.parent / f"{output_file.stem}_metrics.txt"
    with open(metrics_path, "w") as f:
        f.write(f"XGBoost Lead Scorer - Custom Training\n")
        f.write(f"Trained: {datetime.now().isoformat()}\n")
        f.write("=" * 40 + "\n")
        for metric, value in metrics.items():
            f.write(f"{metric}: {value:.4f}\n")
    print(f"✅ Metrics saved to: {metrics_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Train XGBoost Lead Scorer from your own CSV dataset"
    )
    parser.add_argument(
        "--data", "-d",
        required=True,
        help="Path to CSV file with training data"
    )
    parser.add_argument(
        "--output", "-o",
        default="models/custom_lead_scorer.json",
        help="Output path for trained model (default: models/custom_lead_scorer.json)"
    )
    parser.add_argument(
        "--replace", "-r",
        action="store_true",
        help="Replace the active model (lead_scorer_v1.json) with this one"
    )
    
    args = parser.parse_args()
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     🚀 XGBoost Lead Scorer - Custom CSV Training             ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Load data
    df = load_and_prepare_data(args.data)
    
    # Check minimum samples
    if len(df) < 50:
        print(f"\n⚠️ Warning: Only {len(df)} samples. Recommend at least 50 for good results.")
    
    # Train model
    model, scaler, metrics = train_model(df)
    
    # Save model
    save_model(model, scaler, metrics, args.output, args.replace)
    
    print("\n" + "=" * 60)
    print("🎉 TRAINING COMPLETE!")
    print("=" * 60)
    
    if args.replace:
        print(f"\n✅ Active model replaced! Restart backend to use new model.")
    else:
        print(f"\n✅ Model saved to: {args.output}")
        print(f"   To use this model, update MLLeadScorer path or use --replace flag.")


if __name__ == "__main__":
    main()
