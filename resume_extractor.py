import streamlit as st
import pdfplumber
import spacy
import re
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

st.set_page_config(page_title="TalentParse", page_icon="📝", layout="centered")
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; padding: 20px; border-radius: 10px; }
    h1 { color: #2E86C1; text-align: center; }
    .stButton button { background-color: #2E86C1; color: white; }
    </style>
""", unsafe_allow_html=True)

st.title("TalentParse")
st.markdown("**Parse talent from resumes efficiently**")

# Initialize Gemini client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("Please set the GEMINI_API_KEY environment variable in your .env file")
    st.stop()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resumes.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    skills = Column(Text)
    work_experience = Column(Text)
    projects = Column(Text)
    hyperlinks = Column(Text)
    suggested_roles = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Load NLP model
try:
    nlp = spacy.load("en_core_web_sm")
    st.success("spaCy model downloaded successfully!")
except OSError as e:
    st.error("spaCy model 'en_core_web_sm' is not installed. Please check the installation.")
    raise e

def extract_text_and_links(file_path: str):
    """Extract text and hyperlinks from PDF file."""
    text = ""
    hyperlinks = set()
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
            if hasattr(page, 'hyperlinks'):
                for link in page.hyperlinks:
                    uri = link.get('uri')
                    if uri:
                        hyperlinks.add(uri)
    # Also extract URLs present in the text
    text_links = re.findall(r'https?://\S+', text)
    hyperlinks.update(text_links)
    return text, list(hyperlinks)

def extract_info(text: str) -> dict:
    """Extract structured information from text."""
    doc = nlp(text)
    
    # Extract name (assuming it's typically at the top)
    name = text.split('\n')[0].strip() if text else None
    
    # Extract email using regex
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    email = email_match.group(0) if email_match else None
    
    # Extract phone using regex
    phone_match = re.search(r'\+?\d[\d -]{8,}\d', text)
    phone = phone_match.group(0) if phone_match else None
    
    # Extract skills
    skills = []
    skill_patterns = ['Python', 'Java', 'JavaScript', 'React', 'Node.js', 'SQL',
                      'Docker', 'AWS', 'Git', 'HTML', 'CSS', 'Machine Learning']
    for skill in skill_patterns:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            skills.append(skill)
    
    # Extract work experience
    experience = []
    current_exp = {"title": "", "company": "", "points": []}
    in_exp_section = False

    for sent in doc.sents:
        s = sent.text.strip()
        s_lower = s.lower()
        
        if not in_exp_section and any(k in s_lower for k in ["experience", "professional background", "employment"]):
            in_exp_section = True
            continue

        if in_exp_section:
            if any(role in s_lower for role in ["engineer", "developer", "analyst", "consultant", "manager"]):
                if current_exp["title"]:
                    experience.append(current_exp)
                    current_exp = {"title": "", "company": "", "points": []}
                current_exp["title"] = s
            elif any(comp in s_lower for comp in ["at", "inc", "llc", "technologies", "solutions"]):
                current_exp["company"] = s
            else:
                current_exp["points"].append(s)

    if current_exp["title"]:
        experience.append(current_exp)
    
    # Extract projects
    projects = []
    current_project = {'title': '', 'description': []}
    in_projects_section = False

    for sent in doc.sents:
        s = sent.text.strip()
        s_lower = s.lower()
        
        if not in_projects_section and any(k in s_lower for k in ["projects", "project"]):
            in_projects_section = True
            continue

        if in_projects_section:
            if s.isupper() or s.istitle():
                if current_project['title']:
                    projects.append(current_project)
                    current_project = {'title': '', 'description': []}
                current_project['title'] = s
            else:
                current_project['description'].append(s)

    if current_project['title']:
        projects.append(current_project)
    
    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "work_experience": experience,
        "projects": projects
    }

def gemini_insights(text, hyperlinks):
    try:
        # Initialize Gemini client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Configure the model
        model = "gemini-2.0-flash"
        
        # Create content for Gemini request
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"""
                    Here's a resume text:
                    {text}

                    1. Suggest suitable software roles for this candidate.
                    2. Analyze these hyperlinks: {hyperlinks}
                       - What type of links are these? (Portfolio, GitHub, LinkedIn, etc.)
                    3. Provide feedback on strengths based on resume.
                    """)
                ]
            )
        ]

        # Configure Gemini request
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            temperature=0.2  # Lower temperature for more factual responses
        )

        # Get response from Gemini
        response = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config
        ):
            if chunk.text:
                response += chunk.text

        return response

    except Exception as e:
        st.error(f"Error getting Gemini insights: {str(e)}")
        return "Error getting Gemini insights. Please check your API key and try again."

def save_to_database(extracted_info: dict, hyperlinks: list, roles: str = ""):
    """Save extracted information to database."""
    db = SessionLocal()
    db_resume = Resume(
        name=extracted_info.get("name"),
        email=extracted_info.get("email"),
        phone=extracted_info.get("phone"),
        skills=','.join(extracted_info.get("skills", [])),
        work_experience=str(extracted_info.get("work_experience", [])),
        projects=str(extracted_info.get("projects", [])),
        hyperlinks=','.join(hyperlinks),
        suggested_roles=roles
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume.id

def get_all_resumes():
    """Get all resumes from database."""
    db = SessionLocal()
    resumes = db.query(Resume).all()
    return resumes

def main():
    
    # Upload PDF section
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=['pdf'])
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract text and hyperlinks
        text, hyperlinks = extract_text_and_links(uploaded_file.name)
        extracted_info = extract_info(text)
        
        # Get insights from Gemini
        with st.spinner("Getting insights with Gemini..."):
            gemini_output = gemini_insights(text, hyperlinks)
        
        # Save to database
        resume_id = save_to_database(extracted_info, hyperlinks, roles=gemini_output)
        
        # Display results
        st.success("Resume processed successfully!")
        st.subheader("Extracted Information")
        
        # Display in a nice format
        st.markdown("**Name:** " + (extracted_info.get("name", "Not found") or "Not found"))
        st.markdown("**Email:** " + (extracted_info.get("email", "Not found") or "Not found"))
        st.markdown("**Phone:** " + (extracted_info.get("phone", "Not found") or "Not found"))
        
        if extracted_info.get("skills"):
            st.subheader("Skills Found:")
            for skill in extracted_info["skills"]:
                st.write("- " + skill)
        
        if extracted_info.get("work_experience"):
            st.subheader("Work Experience:")
            for exp in extracted_info["work_experience"]:
                st.markdown(f"**Title:** {exp['title']}")
                st.markdown(f"**Company:** {exp['company']}")
                if exp['points']:
                    st.markdown("**Responsibilities:**")
                    for point in exp['points']:
                        st.write("- " + point)
                st.markdown("---")
        
        if extracted_info.get("projects"):
            st.subheader("Projects:")
            for project in extracted_info["projects"]:
                st.markdown(f"**Project Title:** {project['title']}")
                if project["description"]:
                    for line in project["description"]:
                        st.write("- " + line)
                st.markdown("---")
        
        if hyperlinks:
            st.subheader("Hyperlinks Found:")
            for link in hyperlinks:
                st.markdown(f"- [{link}]({link})")
        
        st.subheader("Gemini AI Insights")
        st.markdown(gemini_output)
        
        # Clean up temporary file
        os.remove(uploaded_file.name)
    
    # Display all stored resumes
    st.sidebar.header("All Resumes")
    resumes = get_all_resumes()
    if resumes:
        df = pd.DataFrame([
            {
                "ID": r.id,
                "Name": r.name,
                "Email": r.email,
                "Skills": r.skills,
                "Projects": r.projects,
                "Hyperlinks": r.hyperlinks,
                "Suggested Roles": r.suggested_roles,
                "Uploaded At": r.uploaded_at
            }
            for r in resumes
        ])
        st.sidebar.dataframe(df)

if __name__ == "__main__":
    main() 
