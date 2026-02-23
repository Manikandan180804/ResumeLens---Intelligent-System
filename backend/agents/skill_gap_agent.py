"""
Skill Gap Analysis Agent - Analyzes the gap between resume skills and JD requirements.
"""
import logging
from typing import List, Dict, Any
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


# Skill importance weights
SKILL_WEIGHTS = {
    "programming": 1.5,
    "frameworks": 1.3,
    "ai_ml": 1.4,
    "databases": 1.2,
    "cloud": 1.2,
    "methodologies": 1.0,
    "tools": 0.9
}

# Skill similarity mapping (if candidate has X, they partially match Y)
SKILL_EQUIVALENTS = {
    "react": ["angular", "vue", "next.js"],
    "pytorch": ["tensorflow", "keras"],
    "aws": ["azure", "gcp"],
    "postgresql": ["mysql", "oracle", "sqlite"],
    "mongodb": ["dynamodb", "firebase", "nosql"],
    "docker": ["kubernetes"],
    "python": ["r", "julia"],
    "javascript": ["typescript"],
}


def get_equivalent_credit(skill: str, candidate_skills: List[str]) -> float:
    """Gets partial credit if candidate has equivalent skill."""
    skill_lower = skill.lower()
    for equiv_group_key, equiv_list in SKILL_EQUIVALENTS.items():
        full_group = [equiv_group_key] + equiv_list
        if skill_lower in full_group:
            # Check if candidate has any other skill in this group
            for other_skill in full_group:
                if other_skill != skill_lower and other_skill in [s.lower() for s in candidate_skills]:
                    return 0.5  # 50% credit for equivalent skill
    return 0.0


def calculate_skill_match_score(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str]
) -> Dict[str, Any]:
    """Calculate comprehensive skill match score."""
    candidate_lower = {s.lower() for s in candidate_skills}
    required_lower = [s.lower() for s in required_skills]
    preferred_lower = [s.lower() for s in preferred_skills]

    # Find matches
    matched_required = [s for s in required_lower if s in candidate_lower]
    matched_preferred = [s for s in preferred_lower if s in candidate_lower]
    missing_required = [s for s in required_lower if s not in candidate_lower]
    missing_preferred = [s for s in preferred_lower if s not in candidate_lower]

    # Calculate partial credits
    partial_credit = 0.0
    for skill in missing_required:
        credit = get_equivalent_credit(skill, candidate_skills)
        partial_credit += credit

    # Weighted score calculation
    total_required = len(required_skills) or 1
    total_preferred = len(preferred_skills) or 1

    required_score = (len(matched_required) + partial_credit * 0.5) / total_required
    preferred_score = len(matched_preferred) / total_preferred

    # Combined score (required has more weight)
    raw_score = (required_score * 0.7 + preferred_score * 0.3) * 100
    skill_match_score = round(min(raw_score, 100.0), 2)

    return {
        "skill_match_score": skill_match_score,
        "matched_skills": matched_required + matched_preferred,
        "missing_required_skills": missing_required,
        "missing_preferred_skills": missing_preferred,
        "partial_matches": [s for s in missing_required if get_equivalent_credit(s, candidate_skills) > 0],
        "required_match_pct": round(len(matched_required) / total_required * 100, 1),
        "preferred_match_pct": round(len(matched_preferred) / total_preferred * 100, 1),
        "total_candidate_skills": len(candidate_skills),
        "total_required_skills": len(required_skills),
        "total_preferred_skills": len(preferred_skills),
    }


def generate_skill_gap_categories(
    missing_required: List[str],
    missing_preferred: List[str]
) -> Dict[str, Any]:
    """Categorize skill gaps by technology domain."""
    from backend.agents.resume_parser import SKILL_KEYWORDS

    gap_categories = {}
    all_missing = missing_required + missing_preferred

    for category, skill_list in SKILL_KEYWORDS.items():
        category_gaps = [s for s in all_missing if s.lower() in skill_list]
        if category_gaps:
            priority = "high" if any(s in missing_required for s in category_gaps) else "medium"
            gap_categories[category] = {
                "skills": category_gaps,
                "count": len(category_gaps),
                "priority": priority
            }

    return gap_categories


def skill_gap_analysis_agent(state: AgentState) -> AgentState:
    """Agent that performs comprehensive skill gap analysis."""
    logger.info("Skill Gap Analysis Agent: Starting")

    try:
        candidate_skills = state.get("candidate_skills") or []
        required_skills = state.get("required_skills") or []
        preferred_skills = state.get("preferred_skills") or []

        # Calculate skill match
        analysis = calculate_skill_match_score(candidate_skills, required_skills, preferred_skills)

        # Get gap categories
        gap_categories = generate_skill_gap_categories(
            analysis["missing_required_skills"],
            analysis["missing_preferred_skills"]
        )

        skill_gap_data = {
            **analysis,
            "gap_categories": gap_categories,
            "summary": (
                f"Candidate matches {analysis['required_match_pct']}% of required skills "
                f"and {analysis['preferred_match_pct']}% of preferred skills."
            )
        }

        state["skill_match_score"] = analysis["skill_match_score"]
        state["matched_skills"] = analysis["matched_skills"]
        state["missing_skills"] = analysis["missing_required_skills"]
        state["skill_gap_analysis"] = skill_gap_data
        state["current_step"] = "skill_gap_analysis"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["skill_gap_analysis"]

        logger.info(f"Skill Gap Agent: Score={analysis['skill_match_score']}, Missing={len(analysis['missing_required_skills'])}")

    except Exception as e:
        logger.error(f"Skill Gap Analysis Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Skill gap error: {str(e)}"]
        state["skill_match_score"] = 0.0
        state["matched_skills"] = []
        state["missing_skills"] = []
        state["skill_gap_analysis"] = {}

    return state
