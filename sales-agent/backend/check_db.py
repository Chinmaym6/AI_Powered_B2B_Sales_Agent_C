from app.models.database import SessionLocal
from app.models.tables import Campaign, Lead, Email
from sqlalchemy import desc

def check_db():
    db = SessionLocal()
    try:
        # Check latest campaign
        latest_campaign = db.query(Campaign).order_by(desc(Campaign.created_at)).first()
        if not latest_campaign:
            print("❌ No campaigns found in database!")
            return

        print(f"\n📊 Latest Campaign: {latest_campaign.name}")
        print(f"   ID: {latest_campaign.id}")
        print(f"   Status: {latest_campaign.status}")
        print(f"   Created: {latest_campaign.created_at}")

        # Check leads for this campaign
        leads = db.query(Lead).filter(Lead.campaign_id == latest_campaign.id).all()
        print(f"\n👥 Leads Found: {len(leads)}")
        
        if leads:
            top_lead = leads[0]
            print(f"   Sample Lead: {top_lead.company_name}")
            print(f"   ML Score: {top_lead.ml_score}")
            print(f"   Email: {top_lead.email}")

        # Check emails for this campaign
        emails = db.query(Email).join(Lead).filter(Lead.campaign_id == latest_campaign.id).all()
        print(f"\n✉️ Emails Logged: {len(emails)}")
        
        if emails:
            last_email = emails[-1]
            print(f"   Last Email Subject: {last_email.subject}")
            print(f"   Status: {last_email.status}")
            print(f"   Sent At: {last_email.sent_at}")

    except Exception as e:
        print(f"❌ Error checking DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
