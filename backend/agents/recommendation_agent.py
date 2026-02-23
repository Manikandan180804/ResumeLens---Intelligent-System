"""
Recommendation Agent - Generates actionable recommendations for candidates.
"""
import re
import logging
from typing import List, Dict, Any
from backend.agents.state import AgentState
from backend.agents.scoring_agent import get_score_label

logger = logging.getLogger(__name__)

# Learning resource templates
LEARNING_RESOURCES = {
    "python": "Documentation: docs.python.org | Courses: Coursera Python Specialization",
    "javascript": "MDN Web Docs | freeCodeCamp JavaScript Certificate",
    "react": "Official React Docs (react.dev) | Scrimba React Course",
    "aws": "AWS Training (aws.amazon.com/training) | AWS Certified Solutions Architect",
    "docker": "Docker Getting Started | Docker & Kubernetes Udemy Course",
    "kubernetes": "kubernetes.io/docs | CKAD or CKA Certification",
    "machine learning": "fast.ai | Andrew Ng ML Specialization on Coursera",
    "deep learning": "fast.ai Deep Learning | MIT 6.S191 (YouTube)",
    "nlp": "Hugging Face Course (huggingface.co/learn) | Stanford CS224N",
    "python": "Python.org Tutorial | Python for Data Science Handbook",
    "sql": "Mode Analytics SQL Tutorial | LeetCode SQL Practice",
    "postgresql": "PostgreSQL Official Docs | PostgreSQL Tutorial (postgresqltutorial.com)",
    "mongodb": "MongoDB University Free Courses",
    "tensorflow": "TensorFlow Official Tutorials | DeepLearning.AI TF Certificate",
    "pytorch": "PyTorch Official Tutorials | Fast.ai Libraries",
    "langchain": "LangChain Python Docs | LangChain Academy",
    "git": "Pro Git Book (git-scm.com) | GitHub Learning Lab",
    "agile": "Scrum.org | PMI Agile Certified Practitioner (PMI-ACP)",
}

PRIORITY_CERTS = {
    "aws": "AWS Certified Cloud Practitioner → Solutions Architect",
    "azure": "AZ-900: Azure Fundamentals → AZ-104",
    "gcp": "Google Cloud Associate Cloud Engineer",
    "kubernetes": "CKA (Certified Kubernetes Administrator)",
    "machine learning": "Google Professional ML Engineer | AWS ML Specialty",
    "python": "PCEP/PCAP Python Institute Certifications",
    "data science": "IBM Data Science Professional Certificate",
    "agile": "CSM (Certified Scrum Master) | PMI-ACP",
    "devops": "Docker Certified Associate | Jenkins Certification",
}


def generate_recommendations(
    missing_required: List[str],
    missing_preferred: List[str],
    overall_score: float,
    candidate_skills: List[str],
    job_title: str,
    experience_gap: float,
) -> Dict[str, Any]:
    """Generate structured recommendations."""

    label = get_score_label(overall_score)
    recommendations = []
    certifications = []
    learning_paths = []

    # Score-based overall action
    if overall_score >= 85:
        overall_action = f"🌟 Excellent candidate for {job_title}! Strongly recommend moving to the interview stage."
    elif overall_score >= 70:
        overall_action = f"✅ Strong candidate for {job_title}. Recommend for technical interview."
    elif overall_score >= 55:
        overall_action = f"👍 Reasonable match for {job_title}. Consider for preliminary interview to assess soft skills."
    elif overall_score >= 40:
        overall_action = f"⚠️ Moderate match for {job_title}. Candidate needs skill development before being interview-ready."
    else:
        overall_action = f"❌ Significant skill gaps for {job_title}. Recommend skill development before applying."

    # Specific skill improvement recommendations
    priority_missing = missing_required[:5]  # Focus on top 5 missing required skills
    for skill in priority_missing:
        resource = LEARNING_RESOURCES.get(skill.lower(), f"Search 'learn {skill} online' for resources")
        recommendations.append({
            "skill": skill,
            "priority": "HIGH",
            "action": f"Acquire {skill} skills to meet core job requirements",
            "resources": resource
        })

    # Preferred skills recommendations
    for skill in missing_preferred[:3]:
        resource = LEARNING_RESOURCES.get(skill.lower(), f"Search 'learn {skill} online' for resources")
        recommendations.append({
            "skill": skill,
            "priority": "MEDIUM",
            "action": f"Consider learning {skill} to strengthen your profile",
            "resources": resource
        })

    # Certification recommendations
    combined_missing = missing_required + missing_preferred
    for skill in combined_missing:
        cert = PRIORITY_CERTS.get(skill.lower())
        if cert:
            certifications.append({"skill": skill, "certification": cert})

    # Learning path
    if len(missing_required) > 3:
        learning_paths.append({
            "phase": "Immediate (0-3 months)",
            "focus": f"Master top priority skills: {', '.join(priority_missing[:3])}",
            "outcome": "Become eligible for entry-level positions with this role"
        })
        if missing_required[3:]:
            learning_paths.append({
                "phase": "Short-term (3-6 months)",
                "focus": f"Expand to: {', '.join(missing_required[3:6])}",
                "outcome": "Become a strong candidate for this role"
            })

    # Experience recommendation
    if experience_gap > 0:
        recommendations.append({
            "skill": "Experience",
            "priority": "MEDIUM",
            "action": f"Build {experience_gap:.1f} more years of relevant experience through projects or open source",
            "resources": "GitHub projects, Kaggle competitions, freelance work"
        })

    # Strengths to highlight
    strengths = candidate_skills[:8] if candidate_skills else []

    return {
        "overall_action": overall_action,
        "score_label": label,
        "recommendations": recommendations,
        "certifications": certifications,
        "learning_paths": learning_paths,
        "strengths_to_highlight": strengths,
        "quick_wins": [r for r in recommendations if r["priority"] == "HIGH"][:3]
    }


def clean_recommendation_text(text: str) -> str:
    """Fix common OCR spacing issues (e.g., 'T E X T' -> 'TEXT')."""
    if not text:
        return ""
    # If spaces are found between almost every character, try to collapse them
    # Simple heuristic: if > 50% of spaces are followed/preceded by single letters
    spaces = text.count(' ')
    if spaces > 0 and len(text) / spaces < 3: 
        # Very high frequent spaces - likely OCR artifact
        text = re.sub(r'(?<=\b\w) (?=\w\b)', '', text)
    
    # Cap length for safety
    return text[:200] + "..." if len(text) > 200 else text


def recommendation_agent(state: AgentState) -> AgentState:
    """Agent that generates actionable recommendations."""
    logger.info("Recommendation Agent: Starting")

    try:
        overall_score = state.get("overall_score") or 0.0
        missing_required = state.get("missing_skills") or []
        skill_gap = state.get("skill_gap_analysis") or {}
        missing_preferred = skill_gap.get("missing_preferred_skills", [])
        candidate_skills = state.get("candidate_skills") or []
        job_title = clean_recommendation_text(state.get("job_title") or "the position")

        candidate_exp = state.get("candidate_experience") or 0.0
        required_exp = state.get("experience_required") or 0.0
        experience_gap = max(required_exp - candidate_exp, 0)

        rec_data = generate_recommendations(
            missing_required=missing_required,
            missing_preferred=missing_preferred,
            overall_score=overall_score,
            candidate_skills=candidate_skills,
            job_title=job_title,
            experience_gap=experience_gap,
        )

        # Generate text summary
        # Clean the overall action text as well
        summary_action = clean_recommendation_text(rec_data['overall_action'])

        rec_text = f"""
## Candidate Evaluation Summary

**Match Score**: {overall_score:.1f}/100 — {rec_data['score_label']}

{summary_action}

### Key Strengths
{', '.join(rec_data['strengths_to_highlight']) if rec_data['strengths_to_highlight'] else 'No specific tech strengths detected'}

### Top Priority Skill Gaps
{chr(10).join([f"• **{r['skill']}** (Priority: {r['priority']}): {r['action']}" for r in rec_data['recommendations'][:5]]) if rec_data['recommendations'] else 'No critical skill gaps identified'}

### Recommended Certifications
{chr(10).join([f"• {c['certification']}" for c in rec_data['certifications'][:3]]) if rec_data['certifications'] else 'N/A'}

### Learning Path
{chr(10).join([f"**{lp['phase']}**: {lp['focus']}" for lp in rec_data['learning_paths']]) if rec_data['learning_paths'] else 'Current skills are well-aligned with the role.'}
""".strip()

        state["recommendations"] = rec_data.get("recommendations", [])
        state["recommendation_text"] = rec_text
        state["current_step"] = "recommendation"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["recommendation"]

        logger.info(f"Recommendation Agent: Generated {len(rec_data.get('recommendations', []))} recommendations")

    except Exception as e:
        logger.error(f"Recommendation Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Recommendation error: {str(e)}"]
        state["recommendations"] = []
        state["recommendation_text"] = "Unable to generate recommendations."

    return state
