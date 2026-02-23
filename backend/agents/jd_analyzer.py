"""
Job Description Analysis Agent - Extracts requirements from job descriptions.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from backend.agents.state import AgentState
from backend.agents.resume_parser import extract_skills

logger = logging.getLogger(__name__)


def extract_job_title(text: str) -> str:
    """Extract job title from job description."""
    lines = [l.strip() for l in text.split('\n') if l.strip()][:5]
    title_patterns = [
        r'^(?:job\s+title|position|role)[:\s]+(.+)$',
        r'^(senior|junior|lead|principal|staff)?\s*(.+?(?:engineer|developer|analyst|scientist|architect|manager|designer))',
    ]
    for line in lines:
        for pattern in title_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                title = match.group(1).strip() if len(match.groups()) == 1 else match.group(0).strip()
                return title[:100]
    
    # If no pattern matches, take first line but keep it short
    default_title = lines[0] if lines else "Unknown Position"
    return default_title[:100]


def extract_experience_requirement(text: str) -> float:
    """Extract required years of experience from JD."""
    patterns = [
        r'(\d+)\+?\s*years?\s+of\s+(?:relevant\s+)?experience\s+(?:required|preferred)',
        r'(?:minimum|at\s+least|minimum\s+of)\s+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s+(?:in|of|with)',
        r'(\d+)\s*-\s*(\d+)\s*years?',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            match = matches[0]
            if isinstance(match, tuple):
                return float(min(match))
            return float(match)
    return 0.0


def extract_education_requirement(text: str) -> str:
    """Extract required education level."""
    patterns = [
        (r"ph\.?d\.?|doctorate", "PhD"),
        (r"master'?s?|m\.s\.?|mba", "Master's"),
        (r"bachelor'?s?|b\.s\.?|b\.e\.?|b\.tech", "Bachelor's"),
        (r"associate'?s?", "Associate's"),
        (r"high\s+school|secondary", "High School"),
    ]
    text_lower = text.lower()
    for pattern, label in patterns:
        if re.search(pattern, text_lower):
            return label
    return "Not specified"


def separate_required_preferred(text: str, skills: List[str]) -> Dict[str, List[str]]:
    """Try to separate required vs preferred skills."""
    required = []
    preferred = []

    # Split into sections
    required_section_pattern = r'(?:required|must\s+have|mandatory|essential)[\s\S]*?(?=preferred|nice\s+to\s+have|desired|$)'
    preferred_section_pattern = r'(?:preferred|nice\s+to\s+have|desired|bonus|plus)[\s\S]*'

    req_match = re.search(required_section_pattern, text, re.IGNORECASE)
    pref_match = re.search(preferred_section_pattern, text, re.IGNORECASE)

    req_text = req_match.group(0).lower() if req_match else text.lower()
    pref_text = pref_match.group(0).lower() if pref_match else ""

    for skill in skills:
        skill_lower = skill.lower()
        if pref_text and skill_lower in pref_text:
            preferred.append(skill)
        elif skill_lower in req_text:
            required.append(skill)
        else:
            required.append(skill)  # Default to required

    return {"required": list(set(required)), "preferred": list(set(preferred))}


def extract_soft_skills(text: str) -> List[str]:
    """Extract soft skills from JD."""
    soft_skills = [
        "communication", "teamwork", "leadership", "problem-solving", "critical thinking",
        "adaptability", "creativity", "time management", "collaboration", "interpersonal",
        "presentation", "analytical", "attention to detail", "self-motivated", "proactive",
        "mentoring", "project management", "stakeholder management"
    ]
    text_lower = text.lower()
    found = [s for s in soft_skills if s in text_lower]
    return found


def job_description_analysis_agent(state: AgentState) -> AgentState:
    """Agent that analyzes job descriptions to extract requirements."""
    logger.info("Job Description Analysis Agent: Starting")

    try:
        text = state.get("job_description_text", "")
        if not text:
            state["errors"] = (state.get("errors") or []) + ["Job description text is empty"]
            return state

        title = extract_job_title(text)
        all_skills = extract_skills(text)
        skill_groups = separate_required_preferred(text, all_skills)
        experience_req = extract_experience_requirement(text)
        education_req = extract_education_requirement(text)
        soft_skills = extract_soft_skills(text)

        parsed_job = {
            "title": title,
            "all_skills": all_skills,
            "required_skills": skill_groups["required"],
            "preferred_skills": skill_groups["preferred"],
            "experience_required": experience_req,
            "education_required": education_req,
            "soft_skills": soft_skills,
            "raw_length": len(text)
        }

        state["parsed_job"] = parsed_job
        state["job_title"] = title
        state["required_skills"] = skill_groups["required"]
        state["preferred_skills"] = skill_groups["preferred"]
        state["experience_required"] = experience_req
        state["current_step"] = "job_analysis"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["job_analysis"]

        logger.info(f"Job Analysis Agent: Title='{title}', {len(all_skills)} skills, {experience_req} yrs req")

    except Exception as e:
        logger.error(f"Job Description Analysis Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Job analysis error: {str(e)}"]
        state["parsed_job"] = {}
        state["required_skills"] = []
        state["preferred_skills"] = []

    return state
