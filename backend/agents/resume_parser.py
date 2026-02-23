"""
Resume Parsing Agent - Extracts structured information from raw resume text.
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)

# Comprehensive skill taxonomy
SKILL_KEYWORDS = {
    "programming": [
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "bash",
        "powershell", "sql", "nosql", "html", "css", "sass", "less"
    ],
    "frameworks": [
        "react", "angular", "vue", "next.js", "nuxt.js", "django", "flask",
        "fastapi", "spring", "spring boot", "express", "node.js", "laravel",
        "asp.net", "rails", "tensorflow", "pytorch", "keras", "scikit-learn",
        "pandas", "numpy", "opencv", "langchain", "langgraph", "huggingface"
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "firebase", "sqlite", "oracle", "sql server", "mariadb",
        "neo4j", "influxdb", "clickhouse", "snowflake", "bigquery"
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "jenkins", "gitlab ci", "github actions",
        "circleci", "cloudformation", "helm", "istio", "prometheus", "grafana"
    ],
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "natural language processing", "llm", "gpt", "bert", "transformers",
        "neural network", "reinforcement learning", "data science", "analytics",
        "statistics", "regression", "classification", "clustering", "embedding",
        "vector database", "faiss", "chroma", "rag", "langchain", "openai"
    ],
    "methodologies": [
        "agile", "scrum", "kanban", "devops", "ci/cd", "tdd", "bdd",
        "microservices", "rest api", "graphql", "grpc", "event-driven",
        "design patterns", "solid", "clean architecture", "ddd"
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "slack", "figma", "postman", "swagger", "linux", "unix", "vim",
        "visual studio", "vscode", "intellij", "eclipse", "xcode"
    ]
}

ALL_SKILLS = []
for category, skills in SKILL_KEYWORDS.items():
    ALL_SKILLS.extend(skills)
ALL_SKILLS = list(set(ALL_SKILLS))


def extract_email(text: str) -> Optional[str]:
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def extract_phone(text: str) -> Optional[str]:
    pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def extract_name(text: str) -> Optional[str]:
    """Extract candidate name from first few lines."""
    lines = [l.strip() for l in text.split('\n') if l.strip()][:5]
    for line in lines:
        # Skip lines that look like contact info or headers
        if re.search(r'@|http|www|linkedin|github|resume|cv|curriculum', line, re.I):
            continue
        # Name is likely short (1-4 words) and doesn't have numbers
        words = line.split()
        if 1 <= len(words) <= 4 and not re.search(r'\d', line):
            # Check for typical name patterns
            if all(w[0].isupper() for w in words if len(w) > 1):
                return line
    return lines[0] if lines else None


def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text."""
    text_lower = text.lower()
    found_skills = []

    for skill in ALL_SKILLS:
        # Word boundary check
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return list(set(found_skills))


def extract_experience_years(text: str) -> float:
    """Extract years of experience."""
    patterns = [
        r'(\d+)\+?\s*years?\s+of\s+(?:work\s+)?experience',
        r'experience\s+of\s+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s+(?:work|professional|industry|relevant)',
        r'(\d+)\s*-\s*(\d+)\s*years?\s+of\s+experience',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            match = matches[0]
            if isinstance(match, tuple):
                return float(max(match))
            return float(match)

    # Try to calculate from date ranges in experience section
    date_pattern = r'(20\d{2}|19\d{2})\s*[-–]\s*(20\d{2}|19\d{2}|present|current|now)'
    date_matches = re.findall(date_pattern, text, re.IGNORECASE)

    total_years = 0.0
    for start, end in date_matches:
        try:
            start_yr = int(start)
            end_yr = 2024 if end.lower() in ['present', 'current', 'now'] else int(end)
            if 1990 <= start_yr <= 2024 and start_yr <= end_yr:
                total_years += (end_yr - start_yr)
        except ValueError:
            continue

    return min(total_years, 40.0) if total_years > 0 else 0.0


def extract_education(text: str) -> List[Dict]:
    """Extract education information."""
    education = []
    degrees = {
        "phd": "PhD", "ph.d": "PhD", "doctorate": "PhD",
        "master": "Master's", "m.s": "Master's", "m.sc": "Master's", "mba": "MBA",
        "bachelor": "Bachelor's", "b.s": "Bachelor's", "b.sc": "Bachelor's",
        "b.e": "Bachelor's", "b.tech": "Bachelor's", "b.com": "Bachelor's",
        "associate": "Associate's", "diploma": "Diploma",
        "high school": "High School", "secondary": "High School"
    }

    text_lower = text.lower()
    for key, degree_label in degrees.items():
        if key in text_lower:
            # Try to find the field of study
            pattern = rf'{re.escape(key)}[s.]?[^.]*?(?:in|of)?\s+([A-Za-z\s]+?)(?:\.|,|\n|from|at|\d)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            field = matches[0].strip() if matches else "Not specified"
            education.append({"degree": degree_label, "field": field})

    return education[:3]  # Return top 3


def resume_parsing_agent(state: AgentState) -> AgentState:
    """Agent that parses raw resume text into structured data."""
    logger.info("Resume Parsing Agent: Starting")

    try:
        text = state.get("resume_text", "")
        if not text:
            state["errors"] = (state.get("errors") or []) + ["Resume text is empty"]
            return state

        name = extract_name(text)
        email = extract_email(text)
        phone = extract_phone(text)
        skills = extract_skills(text)
        experience_years = extract_experience_years(text)
        education = extract_education(text)

        # Categorize skills
        categorized_skills = {}
        for category, skill_list in SKILL_KEYWORDS.items():
            matched = [s for s in skills if s in skill_list]
            if matched:
                categorized_skills[category] = matched

        parsed_resume = {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "categorized_skills": categorized_skills,
            "experience_years": experience_years,
            "education": education,
            "raw_length": len(text),
            "skill_count": len(skills)
        }

        state["parsed_resume"] = parsed_resume
        state["candidate_name"] = name
        state["candidate_email"] = email
        state["candidate_skills"] = skills
        state["candidate_experience"] = experience_years
        state["candidate_education"] = [e.get("degree", "") for e in education]
        state["current_step"] = "resume_parsing"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["resume_parsing"]

        logger.info(f"Resume Parsing Agent: Found {len(skills)} skills, {experience_years} years exp")

    except Exception as e:
        logger.error(f"Resume Parsing Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Resume parsing error: {str(e)}"]
        state["parsed_resume"] = {}
        state["candidate_skills"] = []

    return state
