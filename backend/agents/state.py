"""
Agent State definition for LangGraph workflow.
"""
from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """Shared state across all agents in the workflow."""

    # Input data
    resume_text: str
    job_description_text: str
    resume_id: Optional[int]
    job_id: Optional[int]
    evaluation_id: Optional[int]

    # Resume parsing agent output
    parsed_resume: Optional[Dict[str, Any]]
    candidate_name: Optional[str]
    candidate_email: Optional[str]
    candidate_skills: Optional[List[str]]
    candidate_experience: Optional[float]
    candidate_education: Optional[List[str]]

    # Job description analysis agent output
    parsed_job: Optional[Dict[str, Any]]
    job_title: Optional[str]
    required_skills: Optional[List[str]]
    preferred_skills: Optional[List[str]]
    experience_required: Optional[float]

    # Embedding agent output
    resume_embedding: Optional[List[float]]
    job_embedding: Optional[List[float]]

    # Semantic similarity agent output
    semantic_score: Optional[float]
    similar_resumes: Optional[List[Dict]]

    # Skill analysis agent output
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    skill_match_score: Optional[float]
    skill_gap_analysis: Optional[Dict[str, Any]]

    # Scoring agent output
    experience_score: Optional[float]
    education_score: Optional[float]
    overall_score: Optional[float]

    # Recommendation agent output
    recommendations: Optional[List[str]]
    recommendation_text: Optional[str]
    candidate_ranking: Optional[int]

    # Analytics agent output
    analytics_data: Optional[Dict[str, Any]]

    # Workflow metadata
    errors: Optional[List[str]]
    current_step: Optional[str]
    completed_steps: Optional[List[str]]
