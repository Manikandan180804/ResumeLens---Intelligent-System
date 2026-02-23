"""
Demo data seeder - populates the database with sample data for testing.
Run: python seed_demo_data.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import create_tables, SessionLocal, Resume, JobDescription, Evaluation

SAMPLE_RESUMES = [
    {
        "candidate_name": "Arjun Sharma",
        "email": "arjun.sharma@example.com",
        "phone": "+91-9876543210",
        "raw_text": """Arjun Sharma
arjun.sharma@example.com | +91-9876543210 | LinkedIn: linkedin.com/in/arjunsharma

SUMMARY
Senior Machine Learning Engineer with 6 years of experience building production AI systems.
Passionate about NLP, LLMs, and scalable ML infrastructure.

SKILLS
Python, PyTorch, TensorFlow, Scikit-learn, LangChain, LangGraph, FastAPI, Docker, Kubernetes,
AWS, PostgreSQL, Redis, FAISS, Hugging Face, Transformers, NLP, Deep Learning, MLOps, Git,
Linux, Pandas, NumPy, Spark, Kafka

EXPERIENCE
Senior ML Engineer | TechCorp AI | 2021 - Present (3 years)
- Built LLM-powered chatbot serving 1M+ users using LangChain and OpenAI GPT-4
- Designed RAG pipeline using FAISS vector DB reducing hallucinations by 40%
- Led MLOps team of 5 engineers deploying models on Kubernetes/AWS EKS

ML Engineer | DataInnovate | 2019 - 2021 (2 years)
- Developed NLP classification models achieving 94% accuracy
- Built recommendation system using collaborative filtering (Python, Scikit-learn)
- Deployed ML models using FastAPI + Docker on AWS EC2

Junior Data Scientist | Analytics Pvt Ltd | 2018 - 2019 (1 year)
- Performed EDA and built regression/classification models
- Tools: Python, Pandas, Scikit-learn, SQL

EDUCATION
B.Tech in Computer Science | IIT Delhi | 2018
GPA: 8.7/10

CERTIFICATIONS
- AWS Certified Machine Learning Specialty
- Google Professional ML Engineer
""",
        "skills": ["python", "pytorch", "tensorflow", "scikit-learn", "langchain", "langgraph",
                   "fastapi", "docker", "kubernetes", "aws", "postgresql", "redis", "faiss",
                   "nlp", "deep learning", "machine learning"],
        "experience_years": 6.0,
        "education": ["Bachelor's"],
        "parsed_data": {"categorized_skills": {"ai_ml": ["pytorch", "tensorflow", "nlp", "deep learning"]}}
    },
    {
        "candidate_name": "Priya Patel",
        "email": "priya.patel@example.com",
        "phone": "+91-8765432109",
        "raw_text": """Priya Patel
priya.patel@example.com | +91-8765432109

SUMMARY
Full-Stack Developer with 4 years experience in React, Node.js, and cloud services.
Experience with AI integration and building scalable web applications.

SKILLS
JavaScript, TypeScript, React, Next.js, Node.js, Express, PostgreSQL, MongoDB,
Docker, AWS, Git, REST API, GraphQL, Python, Redis, Tailwind CSS, Agile, Scrum

EXPERIENCE
Full Stack Developer | WebTech Solutions | 2022 - Present (2 years)
- Built React/Next.js applications serving 500K+ monthly users
- Designed microservices architecture using Node.js and Docker
- Integrated OpenAI APIs for AI-assisted features

Software Engineer | StartupXYZ | 2020 - 2022 (2 years)
- Developed full-stack web apps using React + Express + MongoDB
- Implemented CI/CD pipelines using GitHub Actions

EDUCATION
B.E. in Information Technology | BITS Pilani | 2020

CERTIFICATIONS
- AWS Certified Developer Associate
""",
        "skills": ["javascript", "typescript", "react", "next.js", "node.js", "express",
                   "postgresql", "mongodb", "docker", "aws", "rest api", "graphql", "python"],
        "experience_years": 4.0,
        "education": ["Bachelor's"],
        "parsed_data": {}
    },
    {
        "candidate_name": "Rahul Verma",
        "email": "rahul.verma@example.com",
        "phone": "+91-7654321098",
        "raw_text": """Rahul Verma
rahul.verma@example.com

SUMMARY
Data Scientist with 2 years of experience in machine learning and data analysis.
Recent graduate with strong ML fundamentals and project experience.

SKILLS
Python, Scikit-learn, Pandas, NumPy, SQL, Tableau, Machine Learning,
Statistics, Matplotlib, Seaborn, Git, Jupyter, R

EXPERIENCE
Data Scientist | Analytics Co | 2024 - Present (0.5 years)
- Builds predictive models using Scikit-learn
- Performs data analysis and visualization

Data Science Intern | Research Lab | 2023 (0.5 years)
- Assisted in NLP projects using Python and NLTK

EDUCATION
M.Sc. Data Science | IIT Bombay | 2024
B.Sc. Statistics | Delhi University | 2022
""",
        "skills": ["python", "scikit-learn", "pandas", "numpy", "sql", "machine learning", "statistics", "r"],
        "experience_years": 1.0,
        "education": ["Master's", "Bachelor's"],
        "parsed_data": {}
    }
]

SAMPLE_JOBS = [
    {
        "title": "Senior Machine Learning Engineer",
        "company": "AI Innovations Ltd",
        "raw_text": """Senior Machine Learning Engineer

Company: AI Innovations Ltd
Location: Bangalore, India (Hybrid)

ABOUT THE ROLE
We are looking for an experienced ML Engineer to lead our AI product team.
You will design, build and deploy production-grade machine learning systems.

REQUIRED SKILLS & QUALIFICATIONS
- 5+ years of experience in machine learning and AI
- Strong proficiency in Python
- Experience with deep learning frameworks: PyTorch or TensorFlow
- Expertise in NLP and Large Language Models (LLMs)
- Experience with LangChain, LangGraph or similar orchestration frameworks
- Vector database experience (FAISS, Chroma, Pinecone)
- MLOps experience: Docker, Kubernetes, CI/CD
- Cloud platform experience: AWS or GCP
- Strong SQL and database skills
- Experience with FastAPI or similar REST frameworks
- Bachelor's degree in Computer Science or related field

PREFERRED SKILLS
- Experience with distributed computing (Spark, Ray)
- Published research or open-source contributions
- AWS ML Specialty or Google ML Engineer certification

RESPONSIBILITIES
- Design and implement ML pipelines and models
- Lead a team of 3-5 ML engineers
- Collaborate with product and data teams
- Mentor junior engineers
""",
        "required_skills": ["python", "pytorch", "tensorflow", "nlp", "machine learning", "langchain",
                            "docker", "kubernetes", "aws", "fastapi", "deep learning", "faiss"],
        "preferred_skills": ["spark", "aws certified", "langgraph"],
        "experience_required": 5.0,
        "education_required": "Bachelor's"
    },
    {
        "title": "Full Stack Developer",
        "company": "TechStartup Inc",
        "raw_text": """Full Stack Developer

Company: TechStartup Inc
Location: Remote

ABOUT THE ROLE
Join our fast-growing startup to build modern web applications.

REQUIRED SKILLS
- 3+ years of full-stack development experience
- Strong React.js / Next.js skills
- Node.js backend development
- TypeScript proficiency
- PostgreSQL or MongoDB database experience
- REST API and GraphQL design
- Docker and cloud deployment (AWS or Azure)
- Git version control
- Agile/Scrum methodology

PREFERRED SKILLS
- React Native or mobile development
- Redis caching
- Microservices architecture experience

EDUCATION
- Bachelor's degree in Computer Science or equivalent

""",
        "required_skills": ["react", "next.js", "node.js", "typescript", "postgresql", "mongodb",
                            "rest api", "graphql", "docker", "aws", "git", "agile"],
        "preferred_skills": ["redis", "microservices"],
        "experience_required": 3.0,
        "education_required": "Bachelor's"
    }
]


def seed_demo_data():
    """Seed the database with sample data."""
    print("=" * 55)
    print("  Resume Intelligence - Demo Data Seeder")
    print("=" * 55)

    create_tables()
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_resumes = db.query(Resume).count()
        if existing_resumes > 0:
            print(f"⚠️  Database already has {existing_resumes} resumes. Skipping seeding.")
            print("   Delete resume_intelligence.db to reset.")
            return

        print("\n[1] Seeding resumes...")
        resume_ids = []
        for r_data in SAMPLE_RESUMES:
            resume = Resume(
                candidate_name=r_data["candidate_name"],
                email=r_data["email"],
                phone=r_data.get("phone"),
                raw_text=r_data["raw_text"],
                skills=r_data["skills"],
                experience_years=r_data["experience_years"],
                education=r_data["education"],
                parsed_data=r_data.get("parsed_data", {}),
                file_name="demo_resume.txt"
            )
            db.add(resume)
            db.flush()
            resume_ids.append(resume.id)
            print(f"   ✅ Added: {r_data['candidate_name']}")

        print("\n[2] Seeding job descriptions...")
        job_ids = []
        for j_data in SAMPLE_JOBS:
            job = JobDescription(
                title=j_data["title"],
                company=j_data["company"],
                raw_text=j_data["raw_text"],
                required_skills=j_data["required_skills"],
                preferred_skills=j_data["preferred_skills"],
                experience_required=j_data["experience_required"],
                education_required=j_data["education_required"]
            )
            db.add(job)
            db.flush()
            job_ids.append(job.id)
            print(f"   ✅ Added: {j_data['title']} @ {j_data['company']}")

        db.commit()

        print(f"\n✅ Seeded {len(resume_ids)} resumes and {len(job_ids)} job descriptions!")
        print("\nNow run evaluations via the Streamlit UI or API:")
        print("  POST /api/evaluate/sync {\"resume_id\": 1, \"job_id\": 1}")
        print("=" * 55)

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
