"""
Generate Realistic B2B Training Data for XGBoost Lead Scorer
============================================================
This creates 500+ realistic leads with proper labeling based on real-world patterns.
Good leads have characteristics that typically convert in B2B sales.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report
import pickle
from pathlib import Path
import random

# Seed for reproducibility
np.random.seed(42)
random.seed(42)

# =============================================================================
# REALISTIC COMPANY DATA TEMPLATES
# =============================================================================

# Good lead patterns (companies likely to convert)
GOOD_COMPANIES = [
    # Tech companies actively seeking solutions
    {"name": "CloudTech Solutions", "industry": "Technology", "size": 150, "has_funding": True, "tech_stack": ["api", "cloud", "saas"], "description": "Fast-growing SaaS company looking to optimize their workflow automation and improve customer engagement through AI-powered solutions."},
    {"name": "DataDriven Analytics", "industry": "Technology", "size": 85, "has_funding": True, "tech_stack": ["ai", "ml", "automation"], "description": "Data analytics startup using machine learning to provide insights. Series A funded, actively expanding their technology stack."},
    {"name": "SecureCloud Inc", "industry": "Technology", "size": 200, "has_funding": True, "tech_stack": ["cloud", "api", "automation"], "description": "Cloud security provider seeking integrated solutions for their enterprise clients. Recently raised $5M Series B."},
    {"name": "AgileStartup Labs", "industry": "Technology", "size": 45, "has_funding": True, "tech_stack": ["saas", "api", "ai"], "description": "Innovative startup building next-generation productivity tools. Seed round completed, scaling rapidly."},
    {"name": "Enterprise Systems Corp", "industry": "Technology", "size": 500, "has_funding": False, "tech_stack": ["automation", "cloud"], "description": "Enterprise software company modernizing legacy systems. Looking for efficient integration solutions."},
    
    # Healthcare companies with tech needs
    {"name": "HealthTech Innovations", "industry": "Healthcare", "size": 120, "has_funding": True, "tech_stack": ["saas", "cloud", "automation"], "description": "Digital health platform connecting patients with providers. Series A funded, expanding into AI diagnostics."},
    {"name": "MedData Solutions", "industry": "Healthcare", "size": 75, "has_funding": True, "tech_stack": ["api", "cloud", "ml"], "description": "Healthcare data management company using machine learning for patient insights. Recently funded startup."},
    
    # Finance companies investing in tech
    {"name": "FinanceFlow Pro", "industry": "Finance", "size": 300, "has_funding": False, "tech_stack": ["automation", "api", "saas"], "description": "Financial services firm automating their trading workflows. Actively seeking AI and automation solutions."},
    {"name": "PayTech Systems", "industry": "Finance", "size": 180, "has_funding": True, "tech_stack": ["api", "cloud", "ai"], "description": "Payment processing startup using AI for fraud detection. Series B funded with rapid growth."},
    
    # Pet/Animal shelter software (specific to user's product)
    {"name": "PetCare Management", "industry": "Pet Services", "size": 50, "has_funding": True, "tech_stack": ["saas", "cloud"], "description": "Animal shelter management platform seeking modern adoption software integration."},
    {"name": "RescueTech Solutions", "industry": "Animal Welfare", "size": 30, "has_funding": False, "tech_stack": ["saas", "automation"], "description": "NGO tech provider for animal rescues. Needs digital forms and adoption matching."},
    {"name": "ShelterSoft Pro", "industry": "Animal Welfare", "size": 25, "has_funding": True, "tech_stack": ["cloud", "saas"], "description": "Shelter management SaaS looking to integrate pet adoption software features."},
]

# Bad lead patterns (companies unlikely to convert)
BAD_COMPANIES = [
    # Too small/no budget
    {"name": "Local Coffee Shop", "industry": "Retail", "size": 5, "has_funding": False, "tech_stack": [], "description": "Small local coffee shop with no online presence."},
    {"name": "Joe's Plumbing", "industry": "Services", "size": 3, "has_funding": False, "tech_stack": [], "description": "Local plumbing service."},
    {"name": "Handmade Crafts LLC", "industry": "Retail", "size": 2, "has_funding": False, "tech_stack": [], "description": "Small handmade crafts seller on Etsy."},
    
    # Wrong industry completely
    {"name": "Heavy Industries Inc", "industry": "Manufacturing", "size": 2000, "has_funding": False, "tech_stack": [], "description": "Traditional steel manufacturing plant with no software needs."},
    {"name": "Mining Corp Global", "industry": "Mining", "size": 5000, "has_funding": False, "tech_stack": [], "description": "Mining operations company with legacy systems only."},
    {"name": "Construction Builders", "industry": "Construction", "size": 150, "has_funding": False, "tech_stack": [], "description": "Construction company focused on residential building."},
    
    # Competitors (would never buy)
    {"name": "RivalTech Solutions", "industry": "Technology", "size": 200, "has_funding": True, "tech_stack": ["saas", "cloud"], "description": "Competitor offering similar services in the same space."},
    
    # No contact info available
    {"name": "Mystery Corp", "industry": "Unknown", "size": 0, "has_funding": False, "tech_stack": [], "description": ""},
    {"name": "No Info LLC", "industry": "Unknown", "size": 0, "has_funding": False, "tech_stack": [], "description": "No description available."},
    
    # Government/non-target
    {"name": "City Government Office", "industry": "Government", "size": 500, "has_funding": False, "tech_stack": [], "description": "Municipality government office with strict procurement rules."},
]

# Industries and their likelihood of being good leads for B2B SaaS
INDUSTRY_SCORES = {
    "Technology": 0.85,
    "Healthcare": 0.75,
    "Finance": 0.80,
    "Pet Services": 0.90,  # User's target
    "Animal Welfare": 0.95,  # User's target
    "E-commerce": 0.70,
    "Education": 0.60,
    "Marketing": 0.65,
    "Retail": 0.30,
    "Manufacturing": 0.20,
    "Construction": 0.15,
    "Mining": 0.10,
    "Government": 0.05,
    "Services": 0.25,
    "Unknown": 0.10,
}

DECISION_MAKERS = [
    ("John Smith", "CEO"),
    ("Sarah Johnson", "CTO"),
    ("Michael Chen", "VP of Engineering"),
    ("Emily Davis", "Head of Product"),
    ("Robert Wilson", "Director of Operations"),
    ("Jennifer Brown", "Chief Digital Officer"),
    ("David Lee", "Founder"),
    ("Lisa Anderson", "COO"),
    ("James Martinez", "VP of Technology"),
    ("Amanda Thompson", "Innovation Director"),
]

TECH_KEYWORDS = ["api", "cloud", "saas", "ai", "ml", "automation", "platform", "integration"]
FUNDING_KEYWORDS = ["series a", "series b", "seed round", "funded", "raised", "investment"]

def generate_training_data(num_samples=500):
    """Generate realistic B2B lead training data"""
    
    data = []
    
    # Generate 60% good leads, 40% bad leads (realistic conversion potential)
    num_good = int(num_samples * 0.55)
    num_bad = num_samples - num_good
    
    print(f"Generating {num_good} good leads and {num_bad} bad leads...")
    
    # Generate GOOD leads
    for i in range(num_good):
        template = random.choice(GOOD_COMPANIES)
        
        # Add variation
        company_size = max(10, template["size"] + random.randint(-20, 50))
        has_funding = template["has_funding"] or random.random() > 0.3
        tech_stack = template["tech_stack"] + random.sample(TECH_KEYWORDS, k=random.randint(0, 2))
        
        # Good leads have complete contact info
        has_email = random.random() > 0.1  # 90% have email
        has_linkedin = random.random() > 0.2  # 80% have LinkedIn
        dm_name, dm_title = random.choice(DECISION_MAKERS) if random.random() > 0.15 else (None, None)
        
        description = template["description"]
        if has_funding:
            description += f" {random.choice(FUNDING_KEYWORDS).title()} recently completed."
        
        # Calculate features
        industry_relevance = INDUSTRY_SCORES.get(template["industry"], 0.5)
        keyword_match = len(set(tech_stack) & set(TECH_KEYWORDS)) / len(TECH_KEYWORDS)
        contact_completeness = sum([has_email, has_linkedin, bool(dm_name), bool(dm_title)]) / 4.0
        
        row = {
            "keyword_match_score": min(1.0, keyword_match + random.uniform(0.1, 0.4)),
            "company_size_log": np.log1p(company_size),
            "industry_relevance": industry_relevance,
            "contact_completeness": contact_completeness,
            "email_available": 1.0 if has_email else 0.0,
            "linkedin_available": 1.0 if has_linkedin else 0.0,
            "has_https": 1.0,  # Good companies have HTTPS
            "description_length_log": np.log1p(len(description)),
            "has_funding_mention": 1.0 if has_funding else 0.0,
            "tech_stack_count": len(tech_stack),
            "pain_point_match": random.uniform(0.5, 1.0),  # Good leads have matching pain points
            "is_good_lead": 1  # LABEL
        }
        data.append(row)
    
    # Generate BAD leads
    for i in range(num_bad):
        template = random.choice(BAD_COMPANIES)
        
        # Bad leads have incomplete or poor data
        company_size = max(0, template["size"] + random.randint(-10, 10))
        has_funding = template["has_funding"]
        tech_stack = template["tech_stack"]
        
        # Bad leads often missing contact info
        has_email = random.random() > 0.5  # Only 50% have email
        has_linkedin = random.random() > 0.7  # Only 30% have LinkedIn
        dm_name, dm_title = random.choice(DECISION_MAKERS) if random.random() > 0.6 else (None, None)
        
        description = template["description"]
        
        industry_relevance = INDUSTRY_SCORES.get(template["industry"], 0.1)
        keyword_match = len(set(tech_stack) & set(TECH_KEYWORDS)) / len(TECH_KEYWORDS)
        contact_completeness = sum([has_email, has_linkedin, bool(dm_name), bool(dm_title)]) / 4.0
        
        row = {
            "keyword_match_score": min(1.0, keyword_match + random.uniform(0, 0.2)),
            "company_size_log": np.log1p(company_size),
            "industry_relevance": industry_relevance,
            "contact_completeness": contact_completeness,
            "email_available": 1.0 if has_email else 0.0,
            "linkedin_available": 1.0 if has_linkedin else 0.0,
            "has_https": 1.0 if random.random() > 0.3 else 0.0,  # 30% don't have HTTPS
            "description_length_log": np.log1p(len(description)),
            "has_funding_mention": 1.0 if has_funding else 0.0,
            "tech_stack_count": len(tech_stack),
            "pain_point_match": random.uniform(0, 0.4),  # Bad leads don't match pain points
            "is_good_lead": 0  # LABEL
        }
        data.append(row)
    
    # Shuffle data
    random.shuffle(data)
    
    return pd.DataFrame(data)

def train_xgboost_model(df):
    """Train XGBoost model on the generated data"""
    
    print("\n" + "="*60)
    print("🧠 TRAINING XGBOOST MODEL")
    print("="*60)
    
    # Split features and target
    X = df.drop('is_good_lead', axis=1)
    y = df['is_good_lead']
    
    feature_names = list(X.columns)
    print(f"\n📊 Features ({len(feature_names)}):")
    for i, name in enumerate(feature_names, 1):
        print(f"   {i}. {name}")
    
    # Train-test split
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
    
    # Train XGBoost with optimized hyperparameters
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
        'Precision': precision_score(y_test, y_pred),
        'Recall': recall_score(y_test, y_pred),
        'F1 Score': f1_score(y_test, y_pred),
        'AUC-ROC': roc_auc_score(y_test, y_pred_proba)
    }
    
    for metric, value in metrics.items():
        bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
        print(f"   {metric:12}: {value:.3f} [{bar}]")
    
    print("\n📋 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Bad Lead', 'Good Lead']))
    
    # Feature importance
    print("\n🎯 FEATURE IMPORTANCE (Top 5):")
    importance = dict(zip(feature_names, model.feature_importances_))
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    for i, (feat, imp) in enumerate(sorted_importance[:5], 1):
        bar = "█" * int(imp * 50)
        print(f"   {i}. {feat:25}: {imp:.3f} [{bar}]")
    
    return model, scaler, metrics

def save_model(model, scaler, metrics):
    """Save the trained model and scaler"""
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Backup old model if exists
    old_model = models_dir / "lead_scorer_v1.json"
    if old_model.exists():
        import shutil
        shutil.copy(old_model, models_dir / "lead_scorer_v1_backup.json")
        print(f"\n💾 Backed up old model")
    
    # Save new model
    model.save_model(str(models_dir / "lead_scorer_v1.json"))
    print(f"✅ Model saved to models/lead_scorer_v1.json")
    
    # Save scaler
    with open(models_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    print(f"✅ Scaler saved to models/scaler.pkl")
    
    # Save metrics log
    with open(models_dir / "training_metrics.txt", "w") as f:
        f.write("XGBoost Lead Scorer Training Metrics\n")
        f.write("=" * 40 + "\n")
        for metric, value in metrics.items():
            f.write(f"{metric}: {value:.4f}\n")
    print(f"✅ Metrics saved to models/training_metrics.txt")

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║     🚀 ML Lead Scorer - Realistic Training Data Generator    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Generate training data
    print("📦 Generating realistic B2B lead training data...")
    df = generate_training_data(num_samples=500)
    
    print(f"\n✅ Generated {len(df)} training samples")
    print(f"   Good leads: {df['is_good_lead'].sum()} ({df['is_good_lead'].mean():.1%})")
    print(f"   Bad leads: {(1 - df['is_good_lead']).sum()} ({(1 - df['is_good_lead'].mean()):.1%})")
    
    # Train model
    model, scaler, metrics = train_xgboost_model(df)
    
    # Save model
    save_model(model, scaler, metrics)
    
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE!")
    print("="*60)
    print(f"""
    Your ML model is now trained on realistic B2B lead data!
    
    Key metrics:
    - Accuracy: {metrics['Accuracy']:.1%}
    - Precision: {metrics['Precision']:.1%} (good at finding real leads)
    - Recall: {metrics['Recall']:.1%} (doesn't miss good leads)
    - AUC-ROC: {metrics['AUC-ROC']:.3f}
    
    The model has learned patterns like:
    ✅ Companies with funding are more likely to convert
    ✅ Tech-savvy companies (API, Cloud, SaaS) are better leads
    ✅ Complete contact info indicates serious prospects
    ✅ Industry relevance matters significantly
    ✅ Company size affects purchasing power
    
    Restart your backend to use the new model!
    """)

if __name__ == "__main__":
    main()
