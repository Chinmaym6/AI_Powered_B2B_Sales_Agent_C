from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
# from pgvector.sqlalchemy import Vector
from .database import Base
import uuid

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    product_name = Column(String, nullable=True)
    product_description = Column(Text, nullable=False)
    target_industry = Column(String)
    target_audience = Column(String, nullable=True)
    company_size = Column(String)
    target_regions = Column(ARRAY(String))
    status = Column(String, default="active")
    product_analysis = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Campaign execution state (for persistence)
    execution_state = Column(String, default="idle")  # idle/running/paused/completed/failed
    current_step = Column(String, nullable=True)  # analyze/search/enrich/score/email
    progress_percentage = Column(Integer, default=0)  # 0-100
    leads_processed = Column(Integer, default=0)
    leads_total = Column(Integer, default=0)
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    can_resume = Column(Boolean, default=True)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    leads = relationship("Lead", back_populates="campaign")
    user = relationship("User", back_populates="campaigns")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Nullable for now to support existing campaigns

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    campaigns = relationship("Campaign", back_populates="user")

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"))
    
    company_name = Column(String, nullable=False)
    industry = Column(String)
    website = Column(String)
    description = Column(Text)
    company_size = Column(Integer)
    location = Column(String)
    
    decision_maker_name = Column(String)
    decision_maker_title = Column(String)
    email = Column(String)
    linkedin_url = Column(String)
    
    rule_based_score = Column(Float)
    ml_score = Column(Float)
    ml_confidence = Column(Float)
    ml_model_version = Column(Integer)
    score_explanation = Column(JSONB)
    
    # description_embedding = Column(Vector(384))
    description_embedding = Column(ARRAY(Float))
    
    # Auto-learning fields for ML improvement
    actual_outcome = Column(Integer, nullable=True)  # 1=good lead, 0=bad lead, None=unknown
    reply_received = Column(Boolean, default=False)
    reply_sentiment = Column(String, nullable=True)  # positive/negative/neutral
    reply_confidence = Column(Float, nullable=True)  # 0.0-1.0
    reply_intent = Column(String, nullable=True)  # interested_demo/not_interested/etc.
    replied_at = Column(DateTime(timezone=True), nullable=True)
    needs_manual_review = Column(Boolean, default=False)
    auto_labeled = Column(Boolean, default=False)  # True if AI auto-labeled the outcome
    
    status = Column(String, default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    campaign = relationship("Campaign", back_populates="leads")
    emails = relationship("Email", back_populates="lead")

class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"))
    subject = Column(String)
    body = Column(Text)
    status = Column(String, default="pending")
    sent_at = Column(DateTime(timezone=True))
    opened_at = Column(DateTime(timezone=True))
    clicked_at = Column(DateTime(timezone=True))
    replied_at = Column(DateTime(timezone=True))
    reply_text = Column(Text)
    reply_sentiment = Column(String)
    reply_intent = Column(String)
    reply_confidence = Column(Float, nullable=True)  # Sentiment confidence 0-1
    processed_for_sentiment = Column(Boolean, default=False)  # Track if analyzed
    message_id = Column(String, nullable=True)  # For email threading
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="emails")

class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_type = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    model_path = Column(Text)
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    num_training_samples = Column(Integer)
    hyperparameters = Column(JSONB)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime(timezone=True), server_default=func.now())

class LeadOutcome(Base):
    __tablename__ = "lead_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"))
    replied = Column(Boolean, default=False)
    reply_sentiment = Column(String)
    converted_to_call = Column(Boolean, default=False)
    converted_to_customer = Column(Boolean, default=False)
    revenue_generated = Column(Float)
    user_quality_rating = Column(Integer)
    notes = Column(Text)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

class ModelFeedback(Base):
    __tablename__ = "model_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"))
    model_version = Column(Integer)
    predicted_score = Column(Float)
    actual_quality = Column(Integer)
    user_id = Column(String)
    feedback_timestamp = Column(DateTime(timezone=True), server_default=func.now())
