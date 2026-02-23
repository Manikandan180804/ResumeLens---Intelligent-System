"""
SQLAlchemy Database Models for Resume Intelligence System
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, JSON, Boolean, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from backend.config import settings

Base = declarative_base()

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)  # structured parsed resume data
    skills = Column(JSON, nullable=True)        # extracted skills list
    experience_years = Column(Float, nullable=True)
    education = Column(JSON, nullable=True)
    file_name = Column(String(255), nullable=True)
    embedding_id = Column(String(100), nullable=True)  # ID in vector store
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    evaluations = relationship("Evaluation", back_populates="resume")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    company = Column(String(200), nullable=True)
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)
    required_skills = Column(JSON, nullable=True)
    preferred_skills = Column(JSON, nullable=True)
    experience_required = Column(Float, nullable=True)
    education_required = Column(String(200), nullable=True)
    embedding_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    evaluations = relationship("Evaluation", back_populates="job_description")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)

    # Scores
    overall_score = Column(Float, nullable=True)
    semantic_similarity_score = Column(Float, nullable=True)
    skill_match_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)

    # Analysis
    skill_gap_analysis = Column(JSON, nullable=True)
    matched_skills = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    recommendation_text = Column(Text, nullable=True)
    candidate_ranking = Column(Integer, nullable=True)  # rank among evaluations for same JD

    # Workflow metadata
    agent_workflow_data = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resume = relationship("Resume", back_populates="evaluations")
    job_description = relationship("JobDescription", back_populates="evaluations")


class SkillTaxonomy(Base):
    __tablename__ = "skill_taxonomy"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(200), unique=True, nullable=False)
    category = Column(String(100), nullable=True)
    aliases = Column(JSON, nullable=True)
    related_skills = Column(JSON, nullable=True)
    demand_score = Column(Float, default=0.5)


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    total_resumes = Column(Integer, default=0)
    total_jobs = Column(Integer, default=0)
    total_evaluations = Column(Integer, default=0)
    avg_match_score = Column(Float, nullable=True)
    top_skills_demand = Column(JSON, nullable=True)
    top_skills_supply = Column(JSON, nullable=True)
    common_skill_gaps = Column(JSON, nullable=True)
    score_distribution = Column(JSON, nullable=True)


def create_tables():
    Base.metadata.create_all(bind=engine)
