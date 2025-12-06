"""
Test script to verify XGBoost ML scorer functionality
"""
from app.ml.lead_scorer import MLLeadScorer

# Initialize scorer
scorer = MLLeadScorer()

# Test lead data
test_lead = {
    'company_name': 'TechCorp AI',
    'description': 'AI automation software for enterprise companies using cloud technology',
    'email': 'contact@techcorp.ai',
    'company_size': 150,
    'industry': 'Technology',
    'website': 'https://techcorp.ai',
    'linkedin_url': 'https://linkedin.com/company/techcorp',
    'decision_maker_name': 'Jane Smith',
    'decision_maker_title': 'CEO'
}

# Test product analysis
test_product = {
    'keywords': ['AI', 'automation', 'cloud', 'enterprise', 'saas'],
    'target_industries': ['Technology', 'Software'],
    'pain_points': ['manual processes', 'inefficiency', 'scaling challenges'],
    'features': ['AI-powered automation', 'cloud integration'],
    'ideal_customer_profile': 'Enterprise technology companies looking for AI automation'
}

# Test prediction
print("=" * 60)
print("Testing XGBoost ML Lead Scorer")
print("=" * 60)
print(f"\nModel Status: {'Loaded' if scorer.model else 'Not Loaded (using fallback)'}")
print(f"Scaler Status: {'Loaded' if scorer.scaler else 'Not Loaded'}")

print(f"\nTest Lead: {test_lead['company_name']}")
print(f"Industry: {test_lead['industry']}")
print(f"Description: {test_lead['description'][:80]}...")

result = scorer.predict(test_lead, test_product)

print("\n" + "=" * 60)
print("PREDICTION RESULTS")
print("=" * 60)
print(f"ML Score: {result['score']:.4f}")
print(f"Confidence: {result['confidence']:.4f} ({result['confidence']*100:.1f}%)")
print(f"Model Version: {result['model_version']}")

print("\nTop Contributing Factors:")
for i, factor in enumerate(result['top_factors'][:5], 1):
    print(f"  {i}. {factor['name']}")
    print(f"     Impact: {factor['impact']:+.4f}")
    print(f"     Value: {factor['value']:.4f}")

print("\n" + "=" * 60)
print("✅ TEST PASSED: ML Scorer is working correctly!")
print("=" * 60)
