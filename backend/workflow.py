"""
LangGraph Workflow Orchestrator - Orchestrates all agents in the evaluation pipeline.
"""
import logging
from typing import Dict, Any

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    try:
        from langgraph.graph import StateGraph
        from langgraph.graph.graph import END
    except ImportError:
        raise ImportError("langgraph is required. Install with: pip install langgraph")

from backend.agents.state import AgentState
from backend.agents.resume_parser import resume_parsing_agent
from backend.agents.jd_analyzer import job_description_analysis_agent
from backend.agents.embedding_agent import embedding_agent, semantic_similarity_agent
from backend.agents.skill_gap_agent import skill_gap_analysis_agent
from backend.agents.scoring_agent import scoring_agent
from backend.agents.recommendation_agent import recommendation_agent
from backend.agents.analytics_agent import analytics_agent, ranking_agent

logger = logging.getLogger(__name__)


def db_persistence_agent(state: AgentState) -> AgentState:
    """Agent that persists evaluation results to the database."""
    logger.info("DB Persistence Agent: Starting")

    try:
        from backend.database import SessionLocal, Evaluation, Resume, JobDescription

        db = SessionLocal()
        try:
            evaluation_id = state.get("evaluation_id")
            if evaluation_id:
                eval_obj = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
                if eval_obj:
                    eval_obj.overall_score = state.get("overall_score")
                    eval_obj.semantic_similarity_score = state.get("semantic_score")
                    eval_obj.skill_match_score = state.get("skill_match_score")
                    eval_obj.experience_score = state.get("experience_score")
                    eval_obj.education_score = state.get("education_score")
                    eval_obj.matched_skills = state.get("matched_skills")
                    eval_obj.missing_skills = state.get("missing_skills")
                    eval_obj.skill_gap_analysis = state.get("skill_gap_analysis")
                    eval_obj.recommendations = state.get("recommendations")
                    eval_obj.recommendation_text = state.get("recommendation_text")
                    eval_obj.candidate_ranking = state.get("candidate_ranking")
                    eval_obj.agent_workflow_data = {
                        "completed_steps": state.get("completed_steps"),
                        "parsed_resume": state.get("parsed_resume"),
                        "parsed_job": state.get("parsed_job"),
                    }
                    eval_obj.status = "completed"

            # Also update the Resume record
            resume_id = state.get("resume_id")
            if resume_id:
                resume_obj = db.query(Resume).filter(Resume.id == resume_id).first()
                if resume_obj:
                    resume_obj.candidate_name = state.get("candidate_name")
                    resume_obj.email = state.get("candidate_email")
                    resume_obj.skills = state.get("candidate_skills")
                    resume_obj.experience_years = state.get("candidate_experience")
                    resume_obj.education = state.get("candidate_education")
                    resume_obj.parsed_data = state.get("parsed_resume")

            # Update JD record
            job_id = state.get("job_id")
            if job_id:
                job_obj = db.query(JobDescription).filter(JobDescription.id == job_id).first()
                if job_obj:
                    parsed_job = state.get("parsed_job") or {}
                    job_obj.required_skills = state.get("required_skills")
                    job_obj.preferred_skills = state.get("preferred_skills")
                    job_obj.experience_required = state.get("experience_required")
                    job_obj.parsed_data = parsed_job

            db.commit()
            logger.info("DB Persistence Agent: Saved to database")

        except Exception as db_err:
            db.rollback()
            logger.error(f"DB persistence error: {db_err}")
            state["errors"] = (state.get("errors") or []) + [f"DB error: {str(db_err)}"]
        finally:
            db.close()

        state["current_step"] = "db_persistence"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["db_persistence"]

    except Exception as e:
        logger.error(f"DB Persistence Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"DB persistence error: {str(e)}"]

    return state


def build_evaluation_graph() -> StateGraph:
    """Build the LangGraph workflow for resume evaluation."""

    workflow = StateGraph(AgentState)

    # Add all agent nodes
    workflow.add_node("resume_parser", resume_parsing_agent)
    workflow.add_node("jd_analyzer", job_description_analysis_agent)
    workflow.add_node("embedder", embedding_agent)
    workflow.add_node("semantic_matcher", semantic_similarity_agent)
    workflow.add_node("skill_gap_analyzer", skill_gap_analysis_agent)
    workflow.add_node("scorer", scoring_agent)
    workflow.add_node("recommender", recommendation_agent)
    workflow.add_node("ranker", ranking_agent)
    workflow.add_node("analytics", analytics_agent)
    workflow.add_node("db_persistence", db_persistence_agent)

    # Define the execution flow
    workflow.set_entry_point("resume_parser")

    # Resume parsing -> JD analysis (can run in parallel conceptually, but sequential for simplicity)
    workflow.add_edge("resume_parser", "jd_analyzer")

    # Both parsers done -> embedding generation
    workflow.add_edge("jd_analyzer", "embedder")

    # Embeddings -> semantic similarity
    workflow.add_edge("embedder", "semantic_matcher")

    # Semantic matcher -> skill gap analysis
    workflow.add_edge("semantic_matcher", "skill_gap_analyzer")

    # Skill gap -> scoring
    workflow.add_edge("skill_gap_analyzer", "scorer")

    # Scoring -> recommendations
    workflow.add_edge("scorer", "recommender")

    # Recommendations -> ranking
    workflow.add_edge("recommender", "ranker")

    # Ranking -> analytics
    workflow.add_edge("ranker", "analytics")

    # Analytics -> DB persistence (final step)
    workflow.add_edge("analytics", "db_persistence")

    # DB persistence -> END
    workflow.add_edge("db_persistence", END)

    return workflow.compile()


# Singleton compiled graph
_graph = None


def get_evaluation_graph():
    global _graph
    if _graph is None:
        _graph = build_evaluation_graph()
    return _graph


async def run_evaluation_workflow(
    resume_text: str,
    job_description_text: str,
    resume_id: int,
    job_id: int,
    evaluation_id: int,
) -> AgentState:
    """Run the full evaluation workflow."""
    logger.info(f"Starting evaluation workflow: resume_id={resume_id}, job_id={job_id}")

    initial_state: AgentState = {
        "resume_text": resume_text,
        "job_description_text": job_description_text,
        "resume_id": resume_id,
        "job_id": job_id,
        "evaluation_id": evaluation_id,
        "parsed_resume": None,
        "candidate_name": None,
        "candidate_email": None,
        "candidate_skills": None,
        "candidate_experience": None,
        "candidate_education": None,
        "parsed_job": None,
        "job_title": None,
        "required_skills": None,
        "preferred_skills": None,
        "experience_required": None,
        "resume_embedding": None,
        "job_embedding": None,
        "semantic_score": None,
        "similar_resumes": None,
        "matched_skills": None,
        "missing_skills": None,
        "skill_match_score": None,
        "skill_gap_analysis": None,
        "experience_score": None,
        "education_score": None,
        "overall_score": None,
        "recommendations": None,
        "recommendation_text": None,
        "candidate_ranking": None,
        "analytics_data": None,
        "errors": [],
        "current_step": None,
        "completed_steps": [],
    }

    graph = get_evaluation_graph()
    final_state = await graph.ainvoke(initial_state)

    logger.info(
        f"Evaluation workflow completed. "
        f"Overall score: {final_state.get('overall_score')}, "
        f"Steps: {final_state.get('completed_steps')}"
    )

    return final_state
