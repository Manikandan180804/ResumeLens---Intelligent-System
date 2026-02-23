"""
Embedding Agent - Generates vector embeddings for resumes and job descriptions.
"""
import logging
from backend.agents.state import AgentState
from backend.vector_store import get_embedding_generator, get_vector_store

logger = logging.getLogger(__name__)


def embedding_agent(state: AgentState) -> AgentState:
    """Agent that generates embeddings and stores them in the vector database."""
    logger.info("Embedding Agent: Starting")

    try:
        gen = get_embedding_generator()
        store = get_vector_store()

        resume_text = state.get("resume_text", "")
        jd_text = state.get("job_description_text", "")

        if resume_text:
            resume_embedding = gen.generate(resume_text)
            state["resume_embedding"] = resume_embedding

            # Also store in vector DB with metadata
            metadata = {
                "type": "resume",
                "resume_id": state.get("resume_id"),
                "candidate_name": state.get("candidate_name", "Unknown"),
                "skills": state.get("candidate_skills", []),
                "experience_years": state.get("candidate_experience", 0),
            }
            doc_id = store.add(resume_embedding, metadata, doc_id=f"resume_{state.get('resume_id')}")
            logger.info(f"Stored resume embedding: {doc_id}")

        if jd_text:
            jd_embedding = gen.generate(jd_text)
            state["job_embedding"] = jd_embedding

            # Store JD embedding
            jd_metadata = {
                "type": "job_description",
                "job_id": state.get("job_id"),
                "title": state.get("job_title", "Unknown"),
                "required_skills": state.get("required_skills", []),
            }
            jd_doc_id = store.add(jd_embedding, jd_metadata, doc_id=f"job_{state.get('job_id')}")
            logger.info(f"Stored JD embedding: {jd_doc_id}")

        state["current_step"] = "embedding"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["embedding"]
        logger.info("Embedding Agent: Completed")

    except Exception as e:
        logger.error(f"Embedding Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Embedding error: {str(e)}"]
        state["resume_embedding"] = []
        state["job_embedding"] = []

    return state


def semantic_similarity_agent(state: AgentState) -> AgentState:
    """Agent that computes semantic similarity between resume and JD."""
    logger.info("Semantic Similarity Agent: Starting")

    try:
        store = get_vector_store()

        resume_emb = state.get("resume_embedding")
        job_emb = state.get("job_embedding")

        if resume_emb and job_emb:
            # Direct similarity between this resume and JD
            similarity = store.get_similarity(resume_emb, job_emb)
            state["semantic_score"] = round(similarity * 100, 2)
        else:
            state["semantic_score"] = 0.0

        # Find similar candidates for ranking context
        if job_emb:
            similar = store.search(job_emb, k=20)
            similar_resumes = [s for s in similar if s.get("type") == "resume"]
            state["similar_resumes"] = similar_resumes[:10]

        state["current_step"] = "semantic_similarity"
        state["completed_steps"] = (state.get("completed_steps") or []) + ["semantic_similarity"]
        logger.info(f"Semantic Similarity Agent: Score={state.get('semantic_score')}")

    except Exception as e:
        logger.error(f"Semantic Similarity Agent error: {e}")
        state["errors"] = (state.get("errors") or []) + [f"Similarity error: {str(e)}"]
        state["semantic_score"] = 0.0
        state["similar_resumes"] = []

    return state
