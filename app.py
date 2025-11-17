import streamlit as st
import pandas as pd
import json
import re
import os
import tempfile
from datetime import datetime
import pdfplumber
import docx
from typing import Dict, List, Any

# Page configuration
st.set_page_config(
    page_title="AI Resume Parser",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .section-header {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 1rem 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF files"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX files"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
    return text

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        st.error(f"Error reading TXT file: {e}")
        return ""

def extract_email(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def extract_phone(text: str) -> List[str]:
    """Extract phone numbers from text"""
    phone_patterns = [
        r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]',
        r'\(\d{3}\)\s*\d{3}[-\.]?\d{4}',
        r'\d{3}[-\.]?\d{3}[-\.]?\d{4}'
    ]
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))
    return phones

def extract_name(text: str) -> str:
    """Extract candidate name (basic heuristic)"""
    lines = text.split('\n')
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and not any(word in line.lower() for word in ['resume', 'cv', 'curriculum', 'vitae', 'phone', 'email', 'linkedin']):
            # Simple name validation (2-3 words, title case)
            words = line.split()
            if 2 <= len(words) <= 4 and all(word.istitle() for word in words if len(word) > 1):
                return line
    return ""

def extract_skills(text: str) -> List[str]:
    """Extract skills using keyword matching"""
    common_skills = [
        'python', 'java', 'javascript', 'html', 'css', 'react', 'angular', 'vue',
        'node.js', 'express', 'django', 'flask', 'fastapi', 'sql', 'nosql',
        'mongodb', 'postgresql', 'mysql', 'aws', 'azure', 'gcp', 'docker',
        'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ci/cd',
        'machine learning', 'ai', 'data analysis', 'pandas', 'numpy',
        'tensorflow', 'pytorch', 'scikit-learn', 'tableau', 'power bi',
        'excel', 'word', 'powerpoint', 'project management', 'agile',
        'scrum', 'jira', 'confluence', 'rest api', 'graphql', 'microservices'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    
    return list(set(found_skills))  # Remove duplicates

def extract_education(text: str) -> List[str]:
    """Extract education information"""
    education_terms = [
        'bachelor', 'master', 'phd', 'doctorate', 'mba', 'bs', 'ms', 'ba', 'ma',
        'university', 'college', 'institute', 'school', 'degree', 'graduated'
    ]
    
    lines = text.split('\n')
    education_lines = []
    
    for line in lines:
        line_lower = line.lower()
        if any(term in line_lower for term in education_terms):
            education_lines.append(line.strip())
    
    return education_lines[:5]  # Return top 5 education lines

def parse_resume_manual(text: str) -> Dict[str, Any]:
    """Manual resume parsing using text analysis"""
    emails = extract_email(text)
    phones = extract_phone(text)
    name = extract_name(text)
    skills = extract_skills(text)
    education = extract_education(text)
    
    # Extract job title (heuristic: look for common title patterns)
    job_titles = []
    title_patterns = [
        r'\b(senior|junior|lead|principal)\s+[a-z]+\s+[a-z]+\b',
        r'\b(software|web|frontend|backend|full.stack|data|devops|cloud)\s+[a-z]+\b',
        r'\b(engineer|developer|architect|analyst|scientist|manager|director)\b'
    ]
    
    for pattern in title_patterns:
        matches = re.findall(pattern, text.lower())
        job_titles.extend(matches)
    
    job_title = job_titles[0].title() if job_titles else ""
    
    return {
        "candidate_name": name,
        "contact_info": {
            "location": "",
            "phone_number": phones[0] if phones else "",
            "email_address": emails,
            "personal_urls": []
        },
        "job_title": job_title,
        "bio": "",
        "work_experience": [],
        "skills": skills,
        "education": education,
        "professional_development": [],
        "other_info": []
    }

def try_pyresparser(file_path: str) -> Dict[str, Any]:
    """Try parsing with pyresparser if available"""
    try:
        from pyresparser import ResumeParser
        data = ResumeParser(file_path).get_extracted_data()
        
        return {
            "candidate_name": data.get('name', ''),
            "contact_info": {
                "location": data.get('location', ''),
                "phone_number": data.get('mobile_number', ''),
                "email_address": [data.get('email', '')] if data.get('email') else [],
                "personal_urls": data.get('links', [])
            },
            "job_title": data.get('designation', ''),
            "bio": "",
            "work_experience": data.get('experience', []),
            "skills": data.get('skills', []),
            "education": data.get('degree', []),
            "professional_development": data.get('certifications', []),
            "other_info": []
        }
    except ImportError:
        st.warning("pyresparser not available. Using manual parsing only.")
        return {}
    except Exception as e:
        st.warning(f"pyresparser failed: {e}")
        return {}

def parse_resume(file_path: str, file_type: str) -> Dict[str, Any]:
    """Main resume parsing function"""
    start_time = datetime.now()
    
    # Extract text based on file type
    if file_type == "application/pdf":
        text = extract_text_from_pdf(file_path)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = extract_text_from_docx(file_path)
    elif file_type == "text/plain":
        text = extract_text_from_txt(file_path)
    else:
        st.error(f"Unsupported file type: {file_type}")
        return {}
    
    if not text.strip():
        st.error("No text could be extracted from the file. The file might be scanned or corrupted.")
        return {}
    
    # Try multiple parsing methods
    parsed_data = {}
    
    # Method 1: Try pyresparser first
    pyres_data = try_pyresparser(file_path)
    if pyres_data and pyres_data.get('candidate_name'):
        parsed_data = pyres_data
    else:
        # Method 2: Use manual parsing
        parsed_data = parse_resume_manual(text)
    
    # Calculate parsing time
    parsing_time = (datetime.now() - start_time).total_seconds()
    
    # Add parsing metadata
    parsed_data["parsing_metadata"] = {
        "parsing_time_seconds": round(parsing_time, 2),
        "file_type": file_type,
        "text_length": len(text),
        "parsing_method": "pyresparser" if pyres_data and pyres_data.get('candidate_name') else "manual"
    }
    
    return parsed_data

def display_parsed_data(data: Dict[str, Any]):
    """Display parsed resume data in a user-friendly format"""
    if not data:
        st.error("No data to display")
        return
    
    # Success message with parsing time
    parsing_time = data.get("parsing_metadata", {}).get("parsing_time_seconds", 0)
    st.markdown(f'<div class="success-box">✅ Resume parsed successfully in {parsing_time} seconds!</div>', unsafe_allow_html=True)
    
    # Create columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Basic Information
        st.markdown('<div class="section-header">👤 Basic Information</div>', unsafe_allow_html=True)
        candidate_name = data.get("candidate_name", "Not found")
        job_title = data.get("job_title", "Not found")
        
        st.write(f"**Name:** {candidate_name}")
        st.write(f"**Job Title:** {job_title}")
        
        # Contact Information
        st.markdown('<div class="section-header">📞 Contact Information</div>', unsafe_allow_html=True)
        contact_info = data.get("contact_info", {})
        
        emails = contact_info.get("email_address", [])
        if emails:
            st.write("**Email:**")
            for email in emails:
                st.write(f"- {email}")
        else:
            st.write("**Email:** Not found")
        
        phone = contact_info.get("phone_number", "")
        st.write(f"**Phone:** {phone if phone else 'Not found'}")
        
        location = contact_info.get("location", "")
        st.write(f"**Location:** {location if location else 'Not found'}")
        
        # Skills
        st.markdown('<div class="section-header">🛠️ Skills</div>', unsafe_allow_html=True)
        skills = data.get("skills", [])
        if skills:
            for skill in skills[:10]:  # Show first 10 skills
                st.write(f"- {skill}")
            if len(skills) > 10:
                st.write(f"*... and {len(skills) - 10} more skills*")
        else:
            st.write("No skills detected")
    
    with col2:
        # Education
        st.markdown('<div class="section-header">🎓 Education</div>', unsafe_allow_html=True)
        education = data.get("education", [])
        if education:
            for edu in education[:5]:  # Show first 5 education entries
                st.write(f"- {edu}")
        else:
            st.write("No education information detected")
        
        # Work Experience (if available)
        work_experience = data.get("work_experience", [])
        if work_experience:
            st.markdown('<div class="section-header">💼 Work Experience</div>', unsafe_allow_html=True)
            for exp in work_experience[:3]:  # Show first 3 experiences
                st.write(f"- {exp}")
        
        # Professional Development
        professional_dev = data.get("professional_development", [])
        if professional_dev:
            st.markdown('<div class="section-header">📚 Professional Development</div>', unsafe_allow_html=True)
            for dev in professional_dev[:3]:
                st.write(f"- {dev}")
    
    # Raw JSON Data (expandable)
    st.markdown('<div class="section-header">📊 Raw JSON Data</div>', unsafe_allow_html=True)
    with st.expander("View Raw Parsed Data"):
        st.json(data)

def main():
    """Main Streamlit application"""
    st.markdown('<h1 class="main-header">AI Resume Parser</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This AI-powered resume parser extracts information from:
        - PDF files
        - DOCX files  
        - TXT files
        
        **Extracts:**
        - Personal Information
        - Contact Details
        - Skills
        - Education
        - Work Experience
        - And more...
        """)
        
        st.header("Instructions")
        st.markdown("""
        1. Upload your resume file
        2. Wait for parsing to complete
        3. Review extracted information
        4. Download results if needed
        """)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Your Resume",
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT"
    )
    
    if uploaded_file is not None:
        # Display file info
        file_details = {
            "Filename": uploaded_file.name,
            "File type": uploaded_file.type,
            "File size": f"{uploaded_file.size / 1024:.2f} KB"
        }
        
        st.markdown('<div class="info-box">📁 File Uploaded Successfully!</div>', unsafe_allow_html=True)
        st.write(file_details)
        
        # Process file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            # Parse resume
            with st.spinner("🔄 Parsing resume... This may take a few seconds."):
                parsed_data = parse_resume(tmp_path, uploaded_file.type)
            
            if parsed_data:
                display_parsed_data(parsed_data)
                
                # Download option
                if st.button("📥 Download Parsed Data as JSON"):
                    json_str = json.dumps(parsed_data, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"parsed_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            else:
                st.error("Failed to parse the resume. Please try with a different file.")
                
        except Exception as e:
            st.error(f"An error occurred during parsing: {str(e)}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    else:
        # Welcome message when no file is uploaded
        st.markdown("""
        <div class="info-box">
        <h3>Welcome to AI Resume Parser!</h3>
        <p>Upload your resume to extract valuable information automatically.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Example of what the parser extracts
        with st.expander("📋 See what information we extract"):
            st.markdown("""
            **Personal Information:**
            - Name
            - Job Title
            - Bio/Summary
            
            **Contact Details:**
            - Email Addresses
            - Phone Numbers
            - Location
            - Personal URLs
            
            **Professional Information:**
            - Skills
            - Education History
            - Work Experience
            - Certifications
            - Professional Development
            """)

if __name__ == "__main__":
    main()