"""
Scoring and Ranking Agent - Computes final scores and candidate rankings.
"""
import logging
from typing import Dict, Any, Optional
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


EDUCATION_SCORES = {
    "PhD": 100,
    "Master's": 90,
    "MBA": 85,
    "Bachelor's": 75,
    "Associate's": 60,
    "Diploma": 50,
    "High School": 30,
    "Not specified": 40
}


def calculate_experience_score(
    candidate_exp: float,
    required_exp: float
) -> float:
    """Score candidate's experience against requirement."""
    if required_exp == 0:
        # No requirement — having experience is still good
        return min(75 + candidate_exp * 2.5, 100)

    ratio = candidate_exp / required_exp
    if ratio >= 1.5:
        return 100.0          # Significantly over-qualified (still max)
    elif ratio >= 1.0:
        return 90.0 + (ratio - 1.0) * 20   # 90-100
    elif ratio >= 0.75:
        return 70.0 + (ratio - 0.75) * 80  # 70-90
    elif ratio >= 0.5:
        return 40.0 + (ratio - 0.5) * 120  # 40-70
    else:
        return max(ratio * 80, 10.0)


def calculate_education_score(
    candidate_education: list,
    required_education: str
) -> float:
    """Score candidate's education."""
    if not candidate_education:
        return 30.0

    # Get the highest level the candidate has
    candidate_max_score = 0
    for edu in candidate_education:
        score = EDUCATION_SCORES.get(edu, 40)
        candidate_max_score = max(candidate_max_score, score)

    required_score = EDUCATION_SCORES.get(required_education or "Not specified", 40)

    if candidate_max_score >= required_score:
        return 100.0
    else:
        # Partial score
        return max(candidate_max_score / required_score * 80, 20)


def calculate_overall_score(
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    education_score: float
) -> float:
    """Weighted overall scoring."""
    weights = {
        "semantic": 0.30,   # Semantic relevance
        "skill": 0.40,      # Skill match is most important
        "experience": 0.20, # Experience matters
        "education": 0.10   # Education baseline
    }
    overall = (
        semantic_score * weights["semantic"] +
        skill_score * weights["skill"] +
        experience_score * weights["experience"] +
        education_score * weights["education"]
    )
    return round(min(overall, 100.0), 2)


def get_score_label(score: float) -> str:
    """Human-readable label for a score."""
    if score >= 85:
        return "Excellent Match"
    elif score >= 70:
        return "Strong Match"
    elif score >= 55:
        return "Good Match"
    elif score >= 40:
        return "Moderate Match"
    elif score >= 25:
        return "Weak Match"
    else:
        return "Poor Match"


def scoring_agent(state: AgentState) -> AgentState:
    """Agent that computes final composite scores."""
    logger.info("Scoring Agent: Starting")

    try:
        candidate_exp = state.get("candidate_experience") or 0.0
        required_exp = state.get("experience_required") or 0.0
        candidate_edu = state.get("candidate_education") or []
        parsed_job = state.get("parsed_job") or {}
        required_edu = parsed_job.get("education_required", "Not specified")

        semantic_score = state.get("semantic_score") or 0.0
        skill_score = state.get("skill_match_score") or 0.0

        exp_score = calculate_experience_score(candidate_exp, required_exp)
        edu_score = calculate_education_score(candidate_edu, required_edu)
        overall = calculate_overall_score(semantic_score, skill_score, exp_score, edu_score)

        state["experience_score"] = round(exp_score, 2)
        state["education_score"] = round(edu_score, 2)
        state["overall_score"] = overall

        logger.info(
            f"Scoring Agent: Overall={overall}, Semantic={semantic_score}, "
            f"Skill={skill_score}, Exp={exp_score:.1f}, Edu={edu_score:.1f}"
        )

        state["current_step"] = "scoring"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["scoring"]

    except Exception as e:
        logger.error(f"Scoring Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Scoring error: {str(e)}"]
        state["experience_score"] = 0.0
        state["education_score"] = 0.0
        state["overall_score"] = 0.0

    return state
