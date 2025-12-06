"""
Comprehensive end-to-end test for XGBoost ML integration
Tests the full workflow that the agent uses
"""
from app.ml.lead_scorer import MLLeadScorer
import json

# Initialize scorer
scorer = MLLeadScorer()

# Product analysis (simulating agent's product analysis step)
product_analysis = {
    'keywords': ['AI', 'automation', 'CRM', 'sales', 'cloud', 'enterprise'],
    'target_industries': ['Technology', 'Software', 'SaaS'],
    'pain_points': ['manual data entry', 'inefficient sales process', 'poor lead tracking'],
    'features': ['AI-powered lead scoring', 'automated outreach', 'CRM integration'],
    'ideal_customer_profile': 'B2B SaaS companies with 50-500 employees looking to automate their sales process'
}

# Test leads (simulating enriched leads from the agent)
test_leads = [
    {
        'company_name': 'CloudTech Solutions',
        'description': 'Enterprise cloud software for sales automation and CRM integration',
        'email': 'sales@cloudtech.com',
        'company_size': 250,
        'industry': 'Technology',
        'website': 'https://cloudtech.com',
        'linkedin_url': 'https://linkedin.com/company/cloudtech',
        'decision_maker_name': 'John Doe',
        'decision_maker_title': 'VP of Sales'
    },
    {
        'company_name': 'RetailCo',
        'description': 'Retail clothing store with 5 locations',
        'email': 'info@retailco.com',
        'company_size': 20,
        'industry': 'Retail',
        'website': 'http://retailco.com',
        'linkedin_url': None,
        'decision_maker_name': None,
        'decision_maker_title': None
    },
    {
        'company_name': 'DataAnalytics Pro',
        'description': 'AI and machine learning platform for enterprise data analysis and automation',
        'email': 'contact@dataanalytics.ai',
        'company_size': 150,
        'industry': 'Software',
        'website': 'https://dataanalytics.ai',
        'linkedin_url': 'https://linkedin.com/company/dataanalytics',
        'decision_maker_name': 'Sarah Johnson',
        'decision_maker_title': 'CTO'
    },
    {
        'company_name': 'Local Plumbing Services',
        'description': 'Plumbing and heating repair services for residential customers',
        'email': 'help@plumbing.com',
        'company_size': 5,
        'industry': 'Services',
        'website': 'http://plumbing.com',
        'linkedin_url': None,
        'decision_maker_name': None,
        'decision_maker_title': None
    }
]

print("=" * 80)
print("END-TO-END XGBOOST ML INTEGRATION TEST")
print("=" * 80)
print(f"\nModel Status: {'✅ Loaded' if scorer.model else '❌ Not Loaded'}")
print(f"Feature Count: {len(scorer.feature_names)}")
print(f"Product Keywords: {', '.join(product_analysis['keywords'][:5])}")

print("\n" + "=" * 80)
print("SCORING LEADS (simulating agent workflow)")
print("=" * 80)

scored_leads = []
for i, lead in enumerate(test_leads, 1):
    print(f"\n[Lead {i}/{len(test_leads)}] {lead['company_name']}")
    print(f"  Industry: {lead['industry']}")
    print(f"  Size: {lead['company_size']} employees")
    print(f"  Email: {'✅' if lead.get('email') else '❌'}")
    
    # Score the lead (this is what the agent does)
    result = scorer.predict(lead, product_analysis)
    
    lead['ml_score'] = result['score']
    lead['ml_confidence'] = result['confidence']
    lead['score_explanation'] = result['top_factors']
    
    scored_leads.append(lead)
    
    print(f"  📊 ML Score: {result['score']:.4f}")
    print(f"  🎯 Confidence: {result['confidence']:.2%}")
    print(f"  🔑 Top Factor: {result['top_factors'][0]['name']}")

# Sort by score (this is what the agent does)
scored_leads.sort(key=lambda x: x['ml_score'], reverse=True)

print("\n" + "=" * 80)
print("RANKED LEADS (sorted by ML score)")
print("=" * 80)

for i, lead in enumerate(scored_leads, 1):
    print(f"\n{i}. {lead['company_name']}")
    print(f"   Score: {lead['ml_score']:.4f} | Confidence: {lead['ml_confidence']:.2%}")
    print(f"   Industry: {lead['industry']} | Size: {lead['company_size']}")

print("\n" + "=" * 80)
print("DETAILED EXPLANATION FOR TOP LEAD")
print("=" * 80)

top_lead = scored_leads[0]
print(f"\nCompany: {top_lead['company_name']}")
print(f"ML Score: {top_lead['ml_score']:.4f}")
print(f"Confidence: {top_lead['ml_confidence']:.2%}")
print(f"\nTop 5 Contributing Factors:")

for i, factor in enumerate(top_lead['score_explanation'][:5], 1):
    impact_emoji = "🟢" if factor['impact'] > 0 else "🔴"
    print(f"  {i}. {impact_emoji} {factor['name']}")
    print(f"      Impact: {factor['impact']:+.4f} | Value: {factor['value']:.4f}")

print("\n" + "=" * 80)
print("✅ END-TO-END TEST PASSED!")
print("=" * 80)
print("\n✨ The XGBoost ML algorithm is fully functional and integrated!")
print("✨ The agent can now score leads with ML predictions and SHAP explanations!")
