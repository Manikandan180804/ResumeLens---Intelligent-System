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
    """Extract job title from job description using progressive strategies."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Patterns for lines we should skip (contact info, generic headers)
    skip_patterns = [
        r'[\w\.-]+@[\w\.-]+\.\w+',
        r'\+?\d[\d\s\-\(\)]{7,}',
        r'https?://\S+',
        r'\b(?:pincode|zip|address|location|office|remote|city|state|country)\b',
        r'\b(?:about\s+(?:us|the\s+company)|benefits|responsibilities|requirements|qualifications|overview)\b',
        r'^[0-9\W]+$',
    ]

    role_suffixes = (
        r'engineer|developer|analyst|scientist|architect|manager|designer|'
        r'representative|assistant|specialist|lead|consultant|director|'
        r'officer|coordinator|intern|associate|executive|administrator|'
        r'technician|operator|supervisor|advisor|strategist'
    )

    def is_skip(line):
        return any(re.search(sp, line, re.IGNORECASE) for sp in skip_patterns)

    # Strategy 1: Explicit label e.g. "Job Title: Data Scientist"
    label_pat = re.compile(
        r'^(?:job\s+title|position(?:\s+title)?|role|opening)[:\s]+(.{3,80})$',
        re.IGNORECASE
    )
    for line in lines[:20]:
        m = label_pat.match(line)
        if m:
            return m.group(1).strip()[:100]

    # Strategy 2: Line starting with a known role keyword (first 30 lines)
    role_line_pat = re.compile(
        rf'^((?:senior|junior|lead|principal|staff|associate|mid[\s-]level|'
        rf'entry[\s-]level|chief)?\s*[\w\s\-/]+?(?:{role_suffixes})[\w\s\-/]{{0,30}})',
        re.IGNORECASE
    )
    for line in lines[:30]:
        if is_skip(line):
            continue
        m = role_line_pat.match(line)
        if m:
            title = m.group(1).strip()
            if len(title) <= 80:
                return title[:100]

    # Strategy 3: Hiring phrase in first 3000 chars
    hire_pat = re.compile(
        rf'(?:seeking|looking\s+for|hiring(?:\s+an?)?|we\s+are\s+hiring\s*[:\-,]?\s*(?:an?)?|'
        rf'role\s+(?:of|is)|position\s+(?:of|is))\s+'
        rf'((?:senior|junior|lead|principal)?\s*[\w\s\-/]{{3,60}}?(?:{role_suffixes}))',
        re.IGNORECASE
    )
    m = hire_pat.search(text[:3000])
    if m:
        return m.group(1).strip()[:100]

    # Strategy 4: Any capitalised role phrase in first 2000 chars
    cap_pat = re.compile(
        rf'\b((?:[A-Z][a-zA-Z\-]{{1,20}}\s+){{0,4}}(?:{role_suffixes}))\b'
    )
    m = cap_pat.search(text[:2000])
    if m:
        candidate = m.group(1).strip()
        if 3 < len(candidate) <= 80:
            return candidate[:100]

    # Strategy 5: First short, clean, non-generic line
    generic_pat = re.compile(
        r'\b(job\s+description|job\s+post(?:ing)?|career|opportunity|'
        r'vacancy|advertisement|about\s+the\s+role|role\s+summary)\b',
        re.IGNORECASE
    )
    for line in lines[:20]:
        if is_skip(line) or generic_pat.search(line):
            continue
        if 3 <= len(line) <= 70:
            return line[:100]

    return "Position Not Specified"


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
