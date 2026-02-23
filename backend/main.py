"""
FastAPI Backend - Main API application with all endpoints.
"""
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import (
    create_tables, get_db, Resume, JobDescription, Evaluation,
    AnalyticsSnapshot, SessionLocal
)
from backend.utils.document_parser import extract_text_from_file, clean_text
from backend.workflow import run_evaluation_workflow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Resume Intelligence API",
    description="Multi-Agent Resume Intelligence and Candidate Evaluation System",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Starting Resume Intelligence API...")
    create_tables()
    logger.info("Database tables created/verified.")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "online", "message": "Resume Intelligence API is running"}


# ─────────────────────────────── Pydantic Schemas ───────────────────────────────


class EvaluationRequest(BaseModel):
    resume_id: int
    job_id: int


class JobDescriptionCreate(BaseModel):
    title: str
    company: Optional[str] = None
    description_text: str


class ResumeResponse(BaseModel):
    id: int
    candidate_name: Optional[str]
    email: Optional[str]
    skills: Optional[List[str]]
    experience_years: Optional[float]
    file_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationResponse(BaseModel):
    id: int
    resume_id: int
    job_description_id: int
    overall_score: Optional[float]
    semantic_similarity_score: Optional[float]
    skill_match_score: Optional[float]
    experience_score: Optional[float]
    education_score: Optional[float]
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    skill_gap_analysis: Optional[Dict[str, Any]]
    recommendations: Optional[List[Dict]]
    recommendation_text: Optional[str]
    candidate_ranking: Optional[int]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────── Root Endpoints ───────────────────────────────


@app.get("/")
async def root():
    return {
        "message": "Resume Intelligence API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ─────────────────────────────── Resume Endpoints ───────────────────────────────


@app.post("/api/resumes/upload", response_model=Dict[str, Any])
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a resume file (PDF/DOCX/TXT) or paste resume text."""
    raw_text = ""
    file_name = None

    if file and file.filename:
        file_bytes = await file.read()
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        raw_text = extract_text_from_file(file_bytes, file.filename)
        file_name = file.filename
    elif resume_text:
        raw_text = resume_text
        file_name = "pasted_resume.txt"

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the provided resume")

    cleaned_text = clean_text(raw_text)

    # Create resume record
    resume = Resume(
        raw_text=cleaned_text,
        file_name=file_name,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {
        "id": resume.id,
        "file_name": file_name,
        "text_length": len(cleaned_text),
        "preview": cleaned_text[:300] + "..." if len(cleaned_text) > 300 else cleaned_text,
        "message": "Resume uploaded successfully. Run evaluation to get analysis."
    }


@app.get("/api/resumes", response_model=List[Dict[str, Any]])
async def list_resumes(db: Session = Depends(get_db)):
    """List all resumes."""
    resumes = db.query(Resume).order_by(Resume.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "candidate_name": r.candidate_name or "Unknown",
            "email": r.email,
            "skills": r.skills or [],
            "skill_count": len(r.skills or []),
            "experience_years": r.experience_years,
            "file_name": r.file_name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "evaluation_count": len(r.evaluations)
        }
        for r in resumes
    ]


@app.get("/api/resumes/{resume_id}", response_model=Dict[str, Any])
async def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get a specific resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {
        "id": resume.id,
        "candidate_name": resume.candidate_name,
        "email": resume.email,
        "phone": resume.phone,
        "skills": resume.skills or [],
        "experience_years": resume.experience_years,
        "education": resume.education or [],
        "parsed_data": resume.parsed_data or {},
        "raw_text_preview": resume.raw_text[:500] if resume.raw_text else "",
        "file_name": resume.file_name,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
    }


@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Delete a resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    db.delete(resume)
    db.commit()
    return {"message": f"Resume {resume_id} deleted"}


# ─────────────────────────────── Job Description Endpoints ───────────────────────────────


@app.post("/api/jobs", response_model=Dict[str, Any])
async def create_job(payload: JobDescriptionCreate, db: Session = Depends(get_db)):
    """Create a new job description via JSON."""
    job = JobDescription(
        title=payload.title,
        company=payload.company,
        raw_text=clean_text(payload.description_text),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "text_length": len(job.raw_text),
        "message": "Job description created successfully."
    }


@app.post("/api/jobs/upload", response_model=Dict[str, Any])
async def upload_job_description(
    file: Optional[UploadFile] = File(None),
    job_text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a job description file (PDF/DOCX/TXT) or paste JD text."""
    raw_text = ""
    file_name = None

    if file and file.filename:
        file_bytes = await file.read()
        if len(file_bytes) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        raw_text = extract_text_from_file(file_bytes, file.filename)
        file_name = file.filename
    elif job_text:
        raw_text = job_text
        file_name = "pasted_jd.txt"

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the provided job description")

    cleaned_text = clean_text(raw_text)

    # If title is not provided, try to extract first line or use default
    if not title:
        first_line = cleaned_text.split('\n')[0][:50]
        title = first_line if len(first_line) > 5 else "Untitled Job"

    # Create job record
    job = JobDescription(
        title=title,
        company=company,
        raw_text=cleaned_text,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "text_length": len(cleaned_text),
        "preview": cleaned_text[:300] + "..." if len(cleaned_text) > 300 else cleaned_text,
        "message": "Job description uploaded successfully."
    }


@app.get("/api/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(db: Session = Depends(get_db)):
    """List all job descriptions."""
    jobs = db.query(JobDescription).order_by(JobDescription.created_at.desc()).all()
    return [
        {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "required_skills": j.required_skills or [],
            "preferred_skills": j.preferred_skills or [],
            "experience_required": j.experience_required,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "evaluation_count": len(j.evaluations)
        }
        for j in jobs
    ]


@app.get("/api/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job description."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found")
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "raw_text_preview": job.raw_text[:500] if job.raw_text else "",
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
        "experience_required": job.experience_required,
        "education_required": job.education_required,
        "parsed_data": job.parsed_data or {},
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job description."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted"}


# ─────────────────────────────── Evaluation Endpoints ───────────────────────────────


@app.post("/api/evaluate", response_model=Dict[str, Any])
async def evaluate_resume(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger evaluation of a resume against a job description."""
    # Validate existences
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume {request.resume_id} not found")

    job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")

    # Create evaluation record
    evaluation = Evaluation(
        resume_id=resume.id,
        job_description_id=job.id,
        status="processing"
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    eval_id = evaluation.id

    # Run workflow in background
    async def run_workflow():
        try:
            await run_evaluation_workflow(
                resume_text=resume.raw_text,
                job_description_text=job.raw_text,
                resume_id=resume.id,
                job_id=job.id,
                evaluation_id=eval_id,
            )
        except Exception as ex:
            logger.error(f"Workflow error for eval {eval_id}: {ex}")
            db2 = SessionLocal()
            try:
                eval_obj = db2.query(Evaluation).filter(Evaluation.id == eval_id).first()
                if eval_obj:
                    eval_obj.status = "failed"
                    eval_obj.error_message = str(ex)
                    db2.commit()
            finally:
                db2.close()

    background_tasks.add_task(run_workflow)

    return {
        "evaluation_id": eval_id,
        "status": "processing",
        "message": "Evaluation started. Use GET /api/evaluations/{id} to check status and results."
    }


@app.post("/api/evaluate/sync", response_model=Dict[str, Any])
async def evaluate_resume_sync(request: EvaluationRequest, db: Session = Depends(get_db)):
    """Synchronous evaluation (waits for result)."""
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume {request.resume_id} not found")

    job = db.query(JobDescription).filter(JobDescription.id == request.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")

    # Create evaluation record
    evaluation = Evaluation(
        resume_id=resume.id,
        job_description_id=job.id,
        status="processing"
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    try:
        final_state = await run_evaluation_workflow(
            resume_text=resume.raw_text,
            job_description_text=job.raw_text,
            resume_id=resume.id,
            job_id=job.id,
            evaluation_id=evaluation.id,
        )

        # Refresh from DB to get latest data
        db.refresh(evaluation)

        return {
            "evaluation_id": evaluation.id,
            "status": "completed",
            "overall_score": final_state.get("overall_score"),
            "semantic_score": final_state.get("semantic_score"),
            "skill_match_score": final_state.get("skill_match_score"),
            "experience_score": final_state.get("experience_score"),
            "education_score": final_state.get("education_score"),
            "candidate_name": final_state.get("candidate_name"),
            "matched_skills": final_state.get("matched_skills") or [],
            "missing_skills": final_state.get("missing_skills") or [],
            "skill_gap_analysis": final_state.get("skill_gap_analysis") or {},
            "recommendations": final_state.get("recommendations") or [],
            "recommendation_text": final_state.get("recommendation_text"),
            "candidate_ranking": final_state.get("candidate_ranking"),
            "completed_steps": final_state.get("completed_steps") or [],
            "errors": final_state.get("errors") or [],
        }

    except Exception as e:
        logger.error(f"Sync evaluation error: {e}")
        evaluation.status = "failed"
        evaluation.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.get("/api/evaluations/{evaluation_id}", response_model=Dict[str, Any])
async def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Get a specific evaluation result."""
    eval_obj = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not eval_obj:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return {
        "id": eval_obj.id,
        "resume_id": eval_obj.resume_id,
        "job_description_id": eval_obj.job_description_id,
        "status": eval_obj.status,
        "overall_score": eval_obj.overall_score,
        "semantic_similarity_score": eval_obj.semantic_similarity_score,
        "skill_match_score": eval_obj.skill_match_score,
        "experience_score": eval_obj.experience_score,
        "education_score": eval_obj.education_score,
        "matched_skills": eval_obj.matched_skills or [],
        "missing_skills": eval_obj.missing_skills or [],
        "skill_gap_analysis": eval_obj.skill_gap_analysis or {},
        "recommendations": eval_obj.recommendations or [],
        "recommendation_text": eval_obj.recommendation_text,
        "candidate_ranking": eval_obj.candidate_ranking,
        "agent_workflow_data": eval_obj.agent_workflow_data or {},
        "error_message": eval_obj.error_message,
        "created_at": eval_obj.created_at.isoformat() if eval_obj.created_at else None,
    }


@app.get("/api/evaluations", response_model=List[Dict[str, Any]])
async def list_evaluations(
    job_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List evaluations, optionally filtered by job."""
    query = db.query(Evaluation).order_by(Evaluation.created_at.desc())
    if job_id:
        query = query.filter(Evaluation.job_description_id == job_id)
    evals = query.all()
    return [
        {
            "id": e.id,
            "resume_id": e.resume_id,
            "job_description_id": e.job_description_id,
            "candidate_name": e.resume.candidate_name if e.resume else "Unknown",
            "job_title": e.job_description.title if e.job_description else "Unknown",
            "overall_score": e.overall_score,
            "skill_match_score": e.skill_match_score,
            "semantic_similarity_score": e.semantic_similarity_score,
            "candidate_ranking": e.candidate_ranking,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in evals
    ]


# ─────────────────────────────── Ranking Endpoints ───────────────────────────────


@app.get("/api/rankings/{job_id}", response_model=List[Dict[str, Any]])
async def get_rankings(job_id: int, db: Session = Depends(get_db)):
    """Get ranked candidates for a specific job."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    evals = (
        db.query(Evaluation)
        .filter(Evaluation.job_description_id == job_id)
        .filter(Evaluation.status == "completed")
        .filter(Evaluation.overall_score.isnot(None))
        .all()
    )

    ranked = sorted(evals, key=lambda e: e.overall_score or 0, reverse=True)
    result = []
    for rank, e in enumerate(ranked, start=1):
        result.append({
            "rank": rank,
            "evaluation_id": e.id,
            "resume_id": e.resume_id,
            "candidate_name": e.resume.candidate_name if e.resume else "Unknown",
            "overall_score": e.overall_score,
            "skill_match_score": e.skill_match_score,
            "semantic_score": e.semantic_similarity_score,
            "experience_score": e.experience_score,
            "matched_skills_count": len(e.matched_skills or []),
            "missing_skills_count": len(e.missing_skills or []),
        })
    return result


# ─────────────────────────────── Analytics Endpoints ───────────────────────────────


@app.get("/api/analytics")
async def get_analytics(db: Session = Depends(get_db)):
    """Get system-wide analytics."""
    from collections import Counter

    resumes = db.query(Resume).all()
    jobs = db.query(JobDescription).all()
    evaluations = db.query(Evaluation).filter(Evaluation.status == "completed").all()

    scores = [e.overall_score for e in evaluations if e.overall_score is not None]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    score_dist = {"0-25": 0, "25-50": 0, "50-75": 0, "75-100": 0}
    for s in scores:
        if s < 25:
            score_dist["0-25"] += 1
        elif s < 50:
            score_dist["25-50"] += 1
        elif s < 75:
            score_dist["50-75"] += 1
        else:
            score_dist["75-100"] += 1

    all_required = []
    for j in jobs:
        all_required.extend(j.required_skills or [])
    top_demand = dict(Counter(all_required).most_common(15))

    all_resume_skills = []
    for r in resumes:
        all_resume_skills.extend(r.skills or [])
    top_supply = dict(Counter(all_resume_skills).most_common(15))

    all_missing = []
    for e in evaluations:
        sg = e.skill_gap_analysis or {}
        all_missing.extend(sg.get("missing_required_skills", []))
    common_gaps = dict(Counter(all_missing).most_common(10))

    return {
        "summary": {
            "total_resumes": len(resumes),
            "total_jobs": len(jobs),
            "total_evaluations": len(evaluations),
            "avg_match_score": avg_score,
        },
        "score_distribution": score_dist,
        "top_skills_in_demand": top_demand,
        "top_skills_in_supply": top_supply,
        "common_skill_gaps": common_gaps,
        "recent_evaluations": [
            {
                "id": e.id,
                "candidate": e.resume.candidate_name if e.resume else "Unknown",
                "job": e.job_description.title if e.job_description else "Unknown",
                "score": e.overall_score,
                "date": e.created_at.isoformat() if e.created_at else None,
            }
            for e in sorted(evaluations, key=lambda x: x.created_at or datetime.min, reverse=True)[:5]
        ]
    }


# ─────────────────────────────── Main ───────────────────────────────


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
