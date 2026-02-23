"""
Analytics Agent - Computes analytics and insights across all evaluations.
"""
import logging
from collections import Counter
from typing import Dict, Any, List
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


def analytics_agent(state: AgentState) -> AgentState:
    """Agent that computes analytics data for dashboards."""
    logger.info("Analytics Agent: Starting")

    try:
        from backend.database import SessionLocal, Evaluation, Resume, JobDescription

        db = SessionLocal()
        try:
            evaluations = db.query(Evaluation).all()
            resumes = db.query(Resume).all()
            jobs = db.query(JobDescription).all()

            total_eval = len(evaluations)
            scores = [e.overall_score for e in evaluations if e.overall_score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0

            # Score distribution
            score_dist = {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}
            for score in scores:
                if score < 25:
                    score_dist["0-25"] += 1
                elif score < 50:
                    score_dist["25-50"] += 1
                elif score < 75:
                    score_dist["50-75"] += 1
                else:
                    score_dist["75-100"] += 1

            # Top skills in demand (from JDs)
            all_required_skills = []
            for job in jobs:
                all_required_skills.extend(job.required_skills or [])
            top_demand = Counter(all_required_skills).most_common(15)

            # Top skills in supply (from resumes)
            all_resume_skills = []
            for resume in resumes:
                all_resume_skills.extend(resume.skills or [])
            top_supply = Counter(all_resume_skills).most_common(15)

            # Common skill gaps
            all_missing = []
            for eval_obj in evaluations:
                skill_gap = eval_obj.skill_gap_analysis or {}
                all_missing.extend(skill_gap.get("missing_required_skills", []))
            common_gaps = Counter(all_missing).most_common(10)

            analytics = {
                "total_resumes": len(resumes),
                "total_jobs": len(jobs),
                "total_evaluations": total_eval,
                "avg_match_score": round(avg_score, 2),
                "score_distribution": score_dist,
                "top_skills_demand": dict(top_demand),
                "top_skills_supply": dict(top_supply),
                "common_skill_gaps": dict(common_gaps),
                "high_match_count": score_dist.get("75-100", 0),
                "low_match_count": score_dist.get("0-25", 0),
            }

        finally:
            db.close()

        state["analytics_data"] = analytics
        state["current_step"] = "analytics"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["analytics"]
        logger.info("Analytics Agent: Completed")

    except Exception as e:
        logger.error(f"Analytics Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Analytics error: {str(e)}"]
        state["analytics_data"] = {}

    return state


def ranking_agent(state: AgentState) -> AgentState:
    """Agent that ranks candidates for a specific job description."""
    logger.info("Ranking Agent: Starting")

    try:
        from backend.database import SessionLocal, Evaluation

        job_id = state.get("job_id")
        current_eval_id = state.get("evaluation_id")
        current_score = state.get("overall_score") or 0.0

        if job_id:
            db = SessionLocal()
            try:
                # Get all (completed) evaluations for this job
                evals = (
                    db.query(Evaluation)
                    .filter(Evaluation.job_description_id == job_id)
                    .filter(Evaluation.overall_score.isnot(None))
                    .all()
                )

                # Sort by score descending
                scores = [(e.id, e.overall_score) for e in evals]
                scores.sort(key=lambda x: x[1], reverse=True)

                # Find rank of current candidate
                rank = None
                for i, (eid, score) in enumerate(scores, start=1):
                    if eid == current_eval_id:
                        rank = i
                        break

                # If not found yet (new eval), compute rank based on score
                if rank is None:
                    rank = sum(1 for _, s in scores if s > current_score) + 1

                state["candidate_ranking"] = rank

            finally:
                db.close()
        else:
            state["candidate_ranking"] = 1

        state["current_step"] = "ranking"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["ranking"]
        logger.info(f"Ranking Agent: Rank={state.get('candidate_ranking')}")

    except Exception as e:
        logger.error(f"Ranking Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Ranking error: {str(e)}"]
        state["candidate_ranking"] = None

    return state
