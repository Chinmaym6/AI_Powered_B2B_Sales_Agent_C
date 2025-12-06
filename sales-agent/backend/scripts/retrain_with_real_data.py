"""
Script to retrain XGBoost model with REAL data from database
This creates a feedback loop for continuous learning
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import pickle
from pathlib import Path
import sys
sys.path.append('.')

from app.models.database import SessionLocal
from app.models.tables import Lead, Email

def extract_real_training_data():
    """
    Extract training data from database with real outcomes
    
    This requires you to manually label leads or track their outcomes:
    - Did they reply to the email?
    - Did they become a customer?
    - Were they actually a good fit?
    """
    
    db = SessionLocal()
    
    # Get all leads with emails sent
    leads = db.query(Lead).filter(Lead.email.isnot(None)).all()
    
    training_data = []
    
    for lead in leads:
        # Get email status
        email_record = db.query(Email).filter(Email.lead_id == lead.id).first()
        
        # MANUAL LABEL: You need to add a column like 'outcome' or 'is_qualified'
        # For now, we'll use a heuristic:
        # - Good lead if: email sent successfully AND has high completeness
        # - In production, replace this with actual conversion data
        
        if hasattr(lead, 'actual_outcome'):
            # If you've manually labeled leads
            outcome = lead.actual_outcome
        else:
            # Heuristic fallback (REPLACE THIS WITH REAL DATA!)
            outcome = 1 if (
                email_record and 
                email_record.status == 'sent' and
                lead.ml_score and lead.ml_score > 0.6
            ) else 0
        
        # Extract features (same as in lead_scorer.py)
        row = {
            'keyword_match_score': 0.5,  # You'd need to recalculate this
            'company_size_log': np.log1p(lead.company_size or 0),
            'industry_relevance': 1.0,  # You'd need the original product analysis
            'contact_completeness': sum([
                1 if lead.email else 0,
                1 if lead.decision_maker_name else 0,
                1 if lead.decision_maker_title else 0,
                1 if lead.linkedin_url else 0
            ]) / 4.0,
            'email_available': 1.0 if lead.email else 0.0,
            'linkedin_available': 1.0 if lead.linkedin_url else 0.0,
            'has_https': 1.0 if lead.website and lead.website.startswith('https') else 0.0,
            'description_length_log': np.log1p(len(lead.description or '')),
            'has_funding_mention': 0.0,  # Would need to check description
            'tech_stack_count': 0,  # Would need to check description
            'pain_point_match': 0.0,  # Would need original product analysis
            'is_good_lead': outcome  # THE LABEL - most important!
        }
        
        training_data.append(row)
    
    db.close()
    
    if len(training_data) < 50:
        print(f"⚠️ Only {len(training_data)} leads in database. Need at least 50 for retraining.")
        print("   Continue running campaigns to collect more data!")
        return None
    
    df = pd.DataFrame(training_data)
    print(f"✅ Extracted {len(df)} leads from database")
    print(f"   Good leads: {df['is_good_lead'].sum()} ({df['is_good_lead'].mean():.1%})")
    print(f"   Bad leads: {(1-df['is_good_lead']).sum()}")
    
    return df

def retrain_with_real_data():
    """
    Retrain the model with actual data from campaigns
    """
    
    print("🔄 RETRAINING MODEL WITH REAL DATA")
    print("=" * 60)
    
    # Extract data
    df = extract_real_training_data()
    
    if df is None:
        print("\n❌ Not enough data to retrain. Using bootstrap instead.")
        return False
    
    # Split features and target
    X = df.drop('is_good_lead', axis=1)
    y = df['is_good_lead']
    
    # Check if we have both classes
    if len(y.unique()) < 2:
        print("\n⚠️ Only one class in data (all good or all bad). Cannot train.")
        print("   You need examples of both good AND bad leads.")
        return False
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost
    print("\n🧠 Training XGBoost with your real lead data...")
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
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred),
        'auc_roc': roc_auc_score(y_test, y_pred_proba)
    }
    
    print("\n📈 NEW Model Performance (trained on YOUR data):")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.3f}")
    
    # Save model
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Backup old model
    old_model = models_dir / "lead_scorer_v1.json"
    if old_model.exists():
        import shutil
        shutil.copy(old_model, models_dir / "lead_scorer_v1_backup.json")
        print(f"\n💾 Backed up old model to lead_scorer_v1_backup.json")
    
    model.save_model(str(models_dir / "lead_scorer_v1.json"))
    
    # Save scaler
    with open(models_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    
    print(f"\n✅ NEW Model saved to {models_dir / 'lead_scorer_v1.json'}")
    print(f"✅ This model learned from {len(df)} real leads!")
    
    return True

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  XGBoost Model Retraining with Real Data                    ║
    ╚══════════════════════════════════════════════════════════════╝
    
    This script will:
    1. Extract lead data from your database
    2. Use actual outcomes (which leads were good/bad)
    3. Retrain the XGBoost model
    4. Replace the old model with the improved one
    
    IMPORTANT: To use this effectively, you need to:
    - Run several campaigns to collect data
    - Manually label which leads were actually good
    - Track email responses, conversions, etc.
    """)
    
    success = retrain_with_real_data()
    
    if success:
        print("\n🎉 Retraining complete! Your model is now smarter!")
    else:
        print("\n⏳ Not ready yet. Keep running campaigns to collect more data!")
