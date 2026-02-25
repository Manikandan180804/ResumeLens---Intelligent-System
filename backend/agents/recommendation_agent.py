"""
Recommendation Agent - Generates actionable recommendations for candidates.
Uses GPT (gpt-4o-mini) when OpenAI is configured, falls back to template logic.
"""
import re
import logging
from typing import List, Dict, Any
from backend.agents.state import AgentState
from backend.agents.scoring_agent import get_score_label
from backend.agents.llm_client import call_llm

logger = logging.getLogger(__name__)

# Learning resource templates (used in both GPT prompt context & template fallback)
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


# ─────────────────────────────── GPT Path ────────────────────────────────────

def _gpt_recommendation(
    overall_score: float,
    score_label: str,
    job_title: str,
    matched_skills: List[str],
    missing_required: List[str],
    missing_preferred: List[str],
    candidate_exp: float,
    required_exp: float,
    candidate_skills: List[str],
) -> str | None:
    """Ask GPT-4o-mini to write a structured evaluation summary. Returns None on failure."""

    system = (
        "You are an expert technical recruiter and career coach. "
        "You write clear, actionable candidate evaluation reports. "
        "Use markdown formatting with ## headers. Be concise and specific. "
        "Do NOT make up skills or experience not listed."
    )

    exp_note = ""
    if required_exp > 0:
        gap = required_exp - candidate_exp
        if gap > 0:
            exp_note = f"The candidate has {candidate_exp:.1f} yrs experience but {required_exp:.1f} yrs are required ({gap:.1f} yr gap)."
        else:
            exp_note = f"The candidate meets or exceeds the {required_exp:.1f} yr experience requirement with {candidate_exp:.1f} yrs."

    user = f"""Write a candidate evaluation report for the following:

**Job Title**: {job_title}
**Overall Match Score**: {overall_score:.1f}/100 — {score_label}
**Matched Skills**: {', '.join(matched_skills) if matched_skills else 'None detected'}
**Missing Required Skills**: {', '.join(missing_required) if missing_required else 'None'}
**Missing Preferred Skills**: {', '.join(missing_preferred) if missing_preferred else 'None'}
**Experience**: {exp_note if exp_note else f'{candidate_exp:.1f} yrs (no specific requirement stated)'}
**Top Candidate Skills**: {', '.join(candidate_skills[:10]) if candidate_skills else 'None detected'}

Write a professional report with these sections:
## Candidate Evaluation Summary
(2-3 sentence overall verdict with a hiring recommendation — Strongly Recommend / Recommend / Consider / Not Recommended)

## Key Strengths
(bullet points of the candidate's strongest selling points for this specific role)

## Skill Gaps & Action Plan
(bullet points: for each missing required skill, suggest a specific resource or certification)

## Learning Path
(Phase 1 - Immediate 0-3 months, Phase 2 - Growth 3-6 months if applicable)

## Final Verdict
(One clear hiring decision sentence)
"""

    return call_llm(system=system, user=user, max_tokens=900, temperature=0.4)


# ─────────────────────────────── Template Fallback ───────────────────────────

def _template_recommendation(
    missing_required: List[str],
    missing_preferred: List[str],
    overall_score: float,
    candidate_skills: List[str],
    job_title: str,
    experience_gap: float,
) -> Dict[str, Any]:
    """Pure template-based recommendations (no API needed)."""

    label = get_score_label(overall_score)
    recommendations = []
    certifications = []
    learning_paths = []

    if overall_score >= 85:
        overall_action = f"🌟 Excellent candidate for {job_title}! Strongly recommend moving to the interview stage."
    elif overall_score >= 70:
        overall_action = f"✅ Strong candidate for {job_title}. Recommend for technical interview."
    elif overall_score >= 55:
        overall_action = f"👍 Reasonable match for {job_title}. Consider for preliminary interview to assess soft skills."
    elif overall_score >= 40:
        if not missing_required and experience_gap > 1.5:
            overall_action = f"⚠️ Moderate match for {job_title}. Skills are aligned, but the candidate significantly lacks the required years of experience."
        elif not missing_required:
            overall_action = f"⚠️ Moderate match for {job_title}. Keywords match, but semantic relevance or experience depth is low."
        else:
            overall_action = f"⚠️ Moderate match for {job_title}. Candidate needs specific skill development before being interview-ready."
    else:
        if not missing_required:
            overall_action = f"❌ Poor match for {job_title}. Despite matching keywords, the experience level and context are not suitable."
        else:
            overall_action = f"❌ Significant skill gaps for {job_title}. Recommend significant upskilling before applying."

    priority_missing = missing_required[:5]
    for skill in priority_missing:
        resource = LEARNING_RESOURCES.get(skill.lower(), f"Search 'learn {skill} online' for resources")
        recommendations.append({
            "skill": skill,
            "priority": "HIGH",
            "action": f"Acquire {skill} skills to meet core job requirements",
            "resources": resource
        })

    for skill in missing_preferred[:3]:
        resource = LEARNING_RESOURCES.get(skill.lower(), f"Search 'learn {skill} online' for resources")
        recommendations.append({
            "skill": skill,
            "priority": "MEDIUM",
            "action": f"Consider learning {skill} to strengthen your profile",
            "resources": resource
        })

    for skill in missing_required + missing_preferred:
        cert = PRIORITY_CERTS.get(skill.lower())
        if cert:
            certifications.append({"skill": skill, "certification": cert})

    if len(missing_required) > 0:
        learning_paths.append({
            "phase": "Immediate (0-3 months)",
            "focus": f"Bridge expertise gap in: {', '.join(priority_missing[:3])}",
            "outcome": "Significantly improve match for this specific role"
        })
        if len(missing_required) > 3 or len(missing_preferred) > 0:
            next_focus = missing_required[3:6] if len(missing_required) > 3 else missing_preferred[:3]
            if next_focus:
                learning_paths.append({
                    "phase": "Growth (3-6 months)",
                    "focus": f"Advance your profile with: {', '.join(next_focus)}",
                    "outcome": "Transition from moderate to strong candidate"
                })
    elif overall_score < 75:
        if missing_preferred:
            learning_paths.append({
                "phase": "Optimization",
                "focus": f"Master preferred skills: {', '.join(missing_preferred[:3])}",
                "outcome": "Gain a competitive edge over other candidates"
            })
        else:
            learning_paths.append({
                "phase": "Deepening",
                "focus": "Deepen existing expertise and build high-quality portfolio projects",
                "outcome": "Demonstrate senior-level mastery in core competencies"
            })

    if experience_gap > 0:
        recommendations.append({
            "skill": "Experience",
            "priority": "MEDIUM",
            "action": f"Build {experience_gap:.1f} more years of relevant experience through projects or open source",
            "resources": "GitHub projects, Kaggle competitions, freelance work"
        })

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


def _build_template_text(rec_data: Dict[str, Any], overall_score: float) -> str:
    """Render template data into markdown string."""
    lp_text = (
        "\n".join([f"**{lp['phase']}**: {lp['focus']}" for lp in rec_data['learning_paths']])
        if rec_data['learning_paths']
        else ("Current skills are exceptionally well-aligned with the role."
              if overall_score >= 80
              else "Focus on deepening core expertise and building specialized projects.")
    )

    return f"""## Candidate Evaluation Summary

**Match Score**: {overall_score:.1f}/100 — {rec_data['score_label']}

{rec_data['overall_action']}

### Key Strengths
{', '.join(rec_data['strengths_to_highlight']) if rec_data['strengths_to_highlight'] else 'No specific tech strengths detected'}

### Top Priority Skill Gaps
{chr(10).join([f"• **{r['skill']}** (Priority: {r['priority']}): {r['action']}" for r in rec_data['recommendations'][:5]]) if rec_data['recommendations'] else ('No critical required skill gaps identified.' if overall_score >= 70 else 'No critical skill gaps detected — focus on deepening existing skills.')}

### Recommended Certifications
{chr(10).join([f"• {c['certification']}" for c in rec_data['certifications'][:3]]) if rec_data['certifications'] else 'N/A'}

### Learning Path
{lp_text}""".strip()


# ─────────────────────────────── Main Agent ──────────────────────────────────

def recommendation_agent(state: AgentState) -> AgentState:
    """Agent that generates actionable recommendations (GPT or template)."""
    logger.info("Recommendation Agent: Starting")

    try:
        overall_score  = state.get("overall_score") or 0.0
        missing_required  = state.get("missing_skills") or []
        skill_gap      = state.get("skill_gap_analysis") or {}
        missing_preferred = skill_gap.get("missing_preferred_skills", [])
        candidate_skills  = state.get("candidate_skills") or []
        matched_skills    = state.get("matched_skills") or []
        job_title      = (state.get("job_title") or "the position")[:120]
        candidate_exp  = state.get("candidate_experience") or 0.0
        required_exp   = state.get("experience_required") or 0.0
        experience_gap = max(required_exp - candidate_exp, 0)
        score_label    = get_score_label(overall_score)

        rec_text = None

        # ── Try GPT first ──────────────────────────────────────────────────
        rec_text = _gpt_recommendation(
            overall_score=overall_score,
            score_label=score_label,
            job_title=job_title,
            matched_skills=matched_skills,
            missing_required=missing_required,
            missing_preferred=missing_preferred,
            candidate_exp=candidate_exp,
            required_exp=required_exp,
            candidate_skills=candidate_skills,
        )

        if rec_text:
            logger.info("Recommendation Agent: Used GPT for recommendations")
            # Still build structured recs for the DB / frontend
            rec_data = _template_recommendation(
                missing_required, missing_preferred, overall_score,
                candidate_skills, job_title, experience_gap
            )
        else:
            # ── Fallback: template ─────────────────────────────────────────
            logger.info("Recommendation Agent: Using template fallback")
            rec_data = _template_recommendation(
                missing_required, missing_preferred, overall_score,
                candidate_skills, job_title, experience_gap
            )
            rec_text = _build_template_text(rec_data, overall_score)

        state["recommendations"]    = rec_data.get("recommendations", [])
        state["recommendation_text"] = rec_text
        state["current_step"]       = "recommendation"
        state["completed_steps"]    = (state.get("completed_steps") or []) + ["recommendation"]

        logger.info(f"Recommendation Agent: {len(rec_data.get('recommendations', []))} structured recs generated")

    except Exception as e:
        logger.error(f"Recommendation Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Recommendation error: {str(e)}"]
        state["recommendations"]    = []
        state["recommendation_text"] = "Unable to generate recommendations."

    return state
